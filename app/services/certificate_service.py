"""
Certificate Generation Service.

Generates blood donation certificates using Pillow.
"""

import asyncio
import os
import stat
from io import BytesIO
from tempfile import NamedTemporaryFile
from datetime import datetime
from pathlib import Path
import re
import uuid
from typing import IO, Callable, Optional
import structlog

# Try to import Pillow, provide fallback if not available
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

logger = structlog.get_logger(__name__)


# New files use a random identifier. Keep accepting historical donor-name and timestamp formats.
_CERT_FILENAME_RE = re.compile(r"[A-Za-z0-9_\-]{1,120}_[0-9]{8}_[0-9]{6}(?:_[0-9a-f]{8})?_certificate\.(png|txt)")


MAX_CERTIFICATE_BYTES = 8 * 1024 * 1024


def _new_filename(extension: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"lc-{uuid.uuid4().hex}_{timestamp}_certificate.{extension}"


def requires_generation_record(filename: str) -> bool:
    return re.match(r"lc-[0-9a-f]{32}_", filename) is not None


def _private_regular_file(info: os.stat_result) -> bool:
    return (stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def read_certificate_bytes(path: Path) -> bytes:
    """Validate and read the same open file for both HTTP and SMTP delivery."""
    before = path.lstat()
    if not _private_regular_file(before) or before.st_size > MAX_CERTIFICATE_BYTES:
        raise ValueError("Invalid certificate file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(before, opened) or not _private_regular_file(opened):
            raise ValueError("Invalid certificate file")
        data = stream.read(MAX_CERTIFICATE_BYTES + 1)
    if not data or len(data) > MAX_CERTIFICATE_BYTES:
        raise ValueError("Invalid certificate size")
    if path.suffix == ".png" and PILLOW_AVAILABLE:
        try:
            with Image.open(BytesIO(data), formats=["PNG"]) as image:
                if image.width * image.height > 16000000:
                    raise ValueError("Invalid certificate dimensions")
                image.verify()
        except (Image.DecompressionBombError, SyntaxError) as exc:
            raise ValueError("Invalid certificate image") from exc
    elif path.suffix == ".txt":
        text = data.decode("utf-8")
        if any(ord(c) < 32 and c not in "\r\n\t" for c in text):
            raise ValueError("Invalid certificate text")
    else:
        raise ValueError("Invalid certificate format")
    return data


class CertificateService:
    """
    Service for generating blood donation certificates.
    
    Uses Pillow to draw donor information on a template image.
    """
    
    def __init__(
        self,
        template_dir: str = "app/static/images/certificate_templates",
        output_dir: str = "app/static/images/certificates",
        font_path: Optional[str] = None,
    ):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.font_path = font_path

    def _ensure_output_dir(self) -> None:
        """Create the output directory on first use, with an actionable error if that is impossible.

        Creating it in __init__ (at import time, before the process drops privileges) hid a
        read-only volume until the first donor tried to get a certificate.
        """
        try:
            self.output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(
                f"Cannot create certificate output directory '{self.output_dir}': {e}. "
                "Create it and give the application user write access, or set the certificate "
                "output directory to a writable path."
            ) from e
        if not os.access(self.output_dir, os.W_OK):
            raise RuntimeError(
                f"Certificate output directory '{self.output_dir}' is not writable by the "
                "application user."
            )

    def _load_font(self, size: int = 25):
        """Load the configured TrueType font, falling back to Pillow's bitmap font."""
        if self.font_path:
            path = Path(self.font_path)
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size)
                except OSError as e:
                    logger.warning(f"CERT_FONT_PATH '{path}' could not be loaded ({e}); using default font")
            else:
                logger.warning(f"CERT_FONT_PATH '{path}' does not exist; using default font")
        return ImageFont.load_default()
    
    async def generate_certificate(
        self,
        donor_name: str,
        donation_date: str,
        blood_group: str,
        location: str,
        template_name: str = "template1.png",
    ) -> str:
        """
        Generate a donation certificate for a donor.
        
        Args:
            donor_name: Name of the donor
            donation_date: Date of donation (formatted string)
            blood_group: Blood group (e.g., "O+", "A-")
            location: Location of donation
            template_name: Template file name
            
        Returns:
            Path to the generated certificate file
        """
        if not re.fullmatch(r"[A-Za-z0-9_-]+\.png", template_name):
            raise ValueError("Invalid certificate template name")
        if not PILLOW_AVAILABLE:
            return await asyncio.to_thread(self._generate_placeholder, donor_name, donation_date, blood_group, location)
        return await asyncio.to_thread(
            self._generate_certificate_sync, donor_name, donation_date, blood_group, location, template_name
        )

    def _generate_certificate_sync(
        self,
        donor_name: str,
        donation_date: str,
        blood_group: str,
        location: str,
        template_name: str,
    ) -> str:
        """Synchronous certificate generation using Pillow."""
        self._ensure_output_dir()
        template_path = self.template_dir / template_name
        
        try:
            with Image.open(template_path, formats=["PNG"]) as source:
                if source.width * source.height > 16_000_000 or source.width < 720 or source.height < 500:
                    raise ValueError("Unsupported certificate template dimensions")
                template = source.convert("RGB")
        except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
            logger.warning("Certificate template unavailable", error=type(exc).__name__)
            return self._create_simple_certificate(donor_name, donation_date, blood_group, location)

        with template:
            draw = ImageDraw.Draw(template)
            font = self._load_font(25)
            for text, position in [
                (donor_name, (328, 187)), (donation_date, (215, 417)),
                (blood_group, (675, 188)), (location, (267, 455)),
            ]:
                draw.text(position, str(text), font=font, fill="black")
            return self._publish_certificate("png", lambda stream: template.save(stream, format="PNG"))

    def _publish_certificate(self, extension: str, write: Callable[[IO[bytes]], object]) -> str:
        # A private temporary file is invisible to the certificate listing. A hard link
        # publishes the completed data atomically and fails if the target already exists.
        temporary = NamedTemporaryFile(dir=self.output_dir, prefix=".lc-cert-", suffix=".tmp", delete=False)
        temp_path = Path(temporary.name)
        try:
            with temporary as stream:
                write(stream.file)
                if not 0 < stream.tell() <= MAX_CERTIFICATE_BYTES:
                    raise ValueError("Invalid generated certificate size")
                stream.flush()
                os.fsync(stream.fileno())
            target = self.output_dir / _new_filename(extension)
            os.link(temp_path, target)
            return str(target)
        finally:
            temp_path.unlink(missing_ok=True)

    def _create_simple_certificate(
        self,
        donor_name: str,
        donation_date: str,
        blood_group: str,
        location: str,
    ) -> str:
        """Create a simple certificate when template is not available."""
        # Create a new white image
        width, height = 800, 600
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        self._ensure_output_dir()

        font = self._load_font(25)
        
        # Draw title
        title = "BLOOD DONATION CERTIFICATE"
        draw.text((width // 2 - 150, 50), title, font=font, fill="darkred")
        
        # Draw content
        lines = [
            "This is to certify that",
            "",
            f"{donor_name}",
            "",
            f"has donated blood on {donation_date}",
            f"Blood Group: {blood_group}",
            f"Location: {location}",
            "",
            "Thank you for saving lives!",
        ]
        
        y_position = 150
        for line in lines:
            draw.text((100, y_position), line, font=font, fill="black")
            y_position += 40
        
        with image:
            return self._publish_certificate("png", lambda stream: image.save(stream, format="PNG"))

    def _generate_placeholder(self, donor_name: str, donation_date: str, blood_group: str, location: str) -> str:
        self._ensure_output_dir()
        content = (f"BLOOD DONATION CERTIFICATE\n\n{donor_name}\nDonation date: {donation_date}\n"
                   f"Blood group: {blood_group}\nLocation: {location}\n")
        if any(ord(c) < 32 and c not in "\r\n\t" for c in content):
            raise ValueError("Invalid certificate text")
        return self._publish_certificate("txt", lambda stream: stream.write(content.encode("utf-8")))

    def _resolve_safe(self, filename: str) -> Optional[Path]:
        if not _CERT_FILENAME_RE.fullmatch(filename or ""):
            return None
        # Keep the original directory entry. Resolving a link before deletion could
        # instead delete the certificate it points to.
        path = self.output_dir.resolve() / filename
        try:
            return path if _private_regular_file(path.lstat()) else None
        except FileNotFoundError:
            return path

    async def get_certificate(self, filename: str) -> Optional[Path]:
        """Get path to an existing certificate."""
        file_path = self._resolve_safe(filename)
        if file_path and file_path.is_file():
            return file_path
        return None
    
    async def list_certificates(self) -> list[str]:
        """List all generated certificates."""
        if not self.output_dir.exists():
            return []
        return sorted(
            f.name
            for pattern in ("*.png", "*.txt")
            for f in self.output_dir.glob(pattern)
            if self._resolve_safe(f.name) is not None and f.is_file()
        )
    
    def entry_remains(self, filename: str) -> bool:
        if not _CERT_FILENAME_RE.fullmatch(filename):
            return False
        try:
            (self.output_dir / filename).lstat()
        except FileNotFoundError:
            return False
        return True

    def purge_expired_files(self, cutoff: float) -> int:
        if not self.output_dir.exists():
            return 0
        deleted = 0
        for path in self.output_dir.iterdir():
            temporary = re.fullmatch(r"\.lc-cert-[a-zA-Z0-9_-]+\.tmp", path.name)
            if not (temporary or _CERT_FILENAME_RE.fullmatch(path.name)):
                continue
            try:
                info = path.lstat()
                # A crash just after publication can leave a second hard link at the temp name.
                managed_file = _private_regular_file(info) or (temporary and stat.S_ISREG(info.st_mode))
                if managed_file and info.st_mtime < cutoff:
                    path.unlink()
                    deleted += 1
            except FileNotFoundError:
                continue
        return deleted

    async def delete_certificate(self, filename: str) -> bool:
        """Delete a certificate file."""
        file_path = self._resolve_safe(filename)
        if file_path is None:
            return False
        try:
            file_path.unlink()
        except FileNotFoundError:
            return False
        return True


# Global service instance
_certificate_service: Optional[CertificateService] = None


def get_certificate_service() -> CertificateService:
    """Get or create certificate service instance."""
    global _certificate_service
    if _certificate_service is None:
        from app.config import get_settings

        settings = get_settings()
        _certificate_service = CertificateService(font_path=settings.CERT_FONT_PATH)
    return _certificate_service
