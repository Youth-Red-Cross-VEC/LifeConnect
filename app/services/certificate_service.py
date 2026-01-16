"""
Certificate Generation Service.

Generates blood donation certificates using Pillow.
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
import structlog

# Try to import Pillow, provide fallback if not available
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

logger = structlog.get_logger(__name__)


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
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
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
        
        # Load font (use default if custom font not available)
        try:
            if self.font_path and Path(self.font_path).exists():
                font = ImageFont.truetype(self.font_path, 25)
            else:
                # Use default font
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        
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
        safe_name = donor_name.replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{safe_name}_{timestamp}_certificate.png"
        file_path = self.output_dir / file_name
        
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
        
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Draw title
        title = "BLOOD DONATION CERTIFICATE"
        draw.text((width // 2 - 150, 50), title, font=font, fill="darkred")
        
        # Draw content
        lines = [
            f"This is to certify that",
            f"",
            f"{donor_name}",
            f"",
            f"has donated blood on {donation_date}",
            f"Blood Group: {blood_group}",
            f"Location: {location}",
            f"",
            f"Thank you for saving lives!",
        ]
        
        y_position = 150
        for line in lines:
            draw.text((100, y_position), line, font=font, fill="black")
            y_position += 40
        
        # Generate filename
        safe_name = donor_name.replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{safe_name}_{timestamp}_certificate.png"
        file_path = self.output_dir / file_name
        
        image.save(file_path)
        
        logger.info(
            "Simple certificate generated (template not found)",
            donor=donor_name,
            file_path=str(file_path),
        )
        
        return str(file_path)
    
    async def _generate_placeholder(self, donor_name: str) -> str:
        """Generate a placeholder text file when Pillow is not available."""
        safe_name = donor_name.replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{safe_name}_{timestamp}_certificate.txt"
        file_path = self.output_dir / file_name
        
        content = f"""
        BLOOD DONATION CERTIFICATE
        
        This certifies that {donor_name} has donated blood.
        
        Note: Image generation requires Pillow package.
        Install with: pip install pillow
        """
        
        with open(file_path, "w") as f:
            f.write(content)
        
        return str(file_path)
    
    async def get_certificate(self, filename: str) -> Optional[Path]:
        """Get path to an existing certificate."""
        file_path = self.output_dir / filename
        if file_path.exists():
            return file_path
        return None
    
    async def list_certificates(self) -> list[str]:
        """List all generated certificates."""
        if not self.output_dir.exists():
            return []
        return [f.name for f in self.output_dir.glob("*.png")]
    
    async def delete_certificate(self, filename: str) -> bool:
        """Delete a certificate file."""
        file_path = self.output_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# Global service instance
_certificate_service: Optional[CertificateService] = None


def get_certificate_service() -> CertificateService:
    """Get or create certificate service instance."""
    global _certificate_service
    if _certificate_service is None:
        _certificate_service = CertificateService()
    return _certificate_service
