"""
Certificate Generation Service.

Generates blood donation certificates using Pillow.
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
import re
import uuid
from typing import Optional
import structlog

# Try to import Pillow, provide fallback if not available
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

logger = structlog.get_logger(__name__)


# Only filenames produced by this service are valid: <name>_<YYYYMMDD>_<HHMMSS>[_<8 hex>]_certificate.<png|txt>.
# Matched with fullmatch (a trailing "$" would also accept a trailing newline) and [0-9] (\d matches other
# scripts' digits). The 8-hex suffix is new; certificates written before it existed still resolve.
_CERT_FILENAME_RE = re.compile(r"[A-Za-z0-9_\-]{1,120}_[0-9]{8}_[0-9]{6}(?:_[0-9a-f]{8})?_certificate\.(png|txt)")


def _new_filename(donor_name: str, extension: str) -> str:
    """Unique per call: two certificates for one donor in the same second must not overwrite each other."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{_safe_name(donor_name)}_{timestamp}_{uuid.uuid4().hex[:8]}_certificate.{extension}"


def _safe_name(donor_name: str) -> str:
    """Reduce a donor name to filesystem-safe characters."""
    cleaned = re.sub(r"[^A-Za-z0-9_\-]", "_", donor_name.strip())
    return cleaned[:60] or "donor"


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
            self.output_dir.mkdir(parents=True, exist_ok=True)
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
        if not PILLOW_AVAILABLE:
            logger.warning("Pillow not installed, using placeholder certificate")
            return await self._generate_placeholder(donor_name)
        
        # Run PIL operations in thread pool (PIL is not async-safe)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate_certificate_sync,
            donor_name,
            donation_date,
            blood_group,
            location,
            template_name,
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
        
        # Check if template exists
        if not template_path.exists():
            logger.warning(f"Template not found: {template_path}")
            # Create a simple blank certificate if template not found
            return self._create_simple_certificate(
                donor_name, donation_date, blood_group, location
            )
        
        # Load template
        template = Image.open(template_path)
        draw = ImageDraw.Draw(template)
        
        font = self._load_font(25)
        
        # Text positions (matching Flask coordinates)
        text_details = [
            (donor_name, (328, 187)),
            (donation_date, (215, 417)),
            (blood_group, (675, 188)),
            (location, (267, 455)),
        ]
        
        # Draw text on template
        for text, position in text_details:
            draw.text(position, str(text), font=font, fill="black")
        
        # Generate unique filename
        file_path = self.output_dir / _new_filename(donor_name, "png")
        
        # Save certificate
        template.save(file_path)
        
        logger.info(
            "Certificate generated",
            donor=donor_name,
            file_path=str(file_path),
        )
        
        return str(file_path)
    
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
        
        file_path = self.output_dir / _new_filename(donor_name, "png")
        
        image.save(file_path)
        
        logger.info(
            "Simple certificate generated (template not found)",
            donor=donor_name,
            file_path=str(file_path),
        )
        
        return str(file_path)
    
    async def _generate_placeholder(self, donor_name: str) -> str:
        """Generate a placeholder text file when Pillow is not available."""
        self._ensure_output_dir()
        file_path = self.output_dir / _new_filename(donor_name, "txt")
        
        content = f"""
        BLOOD DONATION CERTIFICATE
        
        This certifies that {donor_name} has donated blood.
        
        Note: Image generation requires Pillow package.
        Install with: pip install pillow
        """
        
        # Explicit encoding: the platform default (cp1252 on Windows) cannot represent every donor name.
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(file_path)
    
    def _resolve_safe(self, filename: str) -> Optional[Path]:
        """Validate filename pattern and enforce containment in output_dir."""
        if not _CERT_FILENAME_RE.fullmatch(filename or ""):
            return None
        base = self.output_dir.resolve()
        candidate = (base / filename).resolve()
        if candidate.parent != base:
            return None
        return candidate

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
            if _CERT_FILENAME_RE.fullmatch(f.name)
        )
    
    async def delete_certificate(self, filename: str) -> bool:
        """Delete a certificate file."""
        file_path = self._resolve_safe(filename)
        if file_path and file_path.is_file():
            file_path.unlink()
            return True
        return False


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
