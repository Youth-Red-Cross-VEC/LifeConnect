import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from pathlib import Path
import logging
import asyncio
from html import escape as _esc

from app.config import Settings

from app.core.logging import mask_email

logger = logging.getLogger(__name__)


class EmailService:
    """
    Async email service for sending notifications.
    
    Supports:
    - Plain text and HTML emails
    - Attachments (for certificates)
    - Batch sending
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachment_path: Optional[Path] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email asynchronously.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text fallback
            attachment_path: Optional file to attach
            bcc: Extra recipients that receive the message without appearing in any header
            
        Returns:
            True if sent successfully
        """
        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.settings.MAIL_FROM
            message["To"] = to
            message["Subject"] = subject

            # Add text part
            if text_body:
                message.attach(MIMEText(text_body, "plain"))

            # Add HTML part
            message.attach(MIMEText(html_body, "html"))

            # Add attachment if provided
            if attachment_path and attachment_path.exists():
                await self._attach_file(message, attachment_path)

            # Send email. Bcc recipients go in the SMTP envelope only, never in a header.
            await aiosmtplib.send(
                message,
                recipients=[to, *(bcc or [])],
                hostname=self.settings.MAIL_SERVER,
                port=self.settings.MAIL_PORT,
                username=self.settings.MAIL_USERNAME,
                password=self.settings.MAIL_PASSWORD,
                start_tls=self.settings.MAIL_USE_TLS,
            )

            logger.info(f"Email sent successfully to {mask_email(to)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {mask_email(to)}: {type(e).__name__}")
            return False

    def _build_message(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachment_path: Optional[Path] = None,
    ) -> MIMEMultipart:
        """Build one MIME message. Shared by single and batched sends."""
        message = MIMEMultipart("alternative")
        message["From"] = self.settings.MAIL_FROM
        message["To"] = to
        message["Subject"] = subject
        if text_body:
            message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))
        if attachment_path and attachment_path.exists():
            self._attach_file_sync(message, attachment_path)
        return message

    def _attach_file_sync(self, message: MIMEMultipart, file_path: Path) -> None:
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=file_path.name)
            message.attach(part)

    async def send_many(self, messages: List[dict]) -> int:
        """Send several messages over ONE SMTP connection.

        Returns how many were sent. A failure on one message does not abort the rest (the old
        per-message background task had the same behaviour, but opened a connection each time).
        """
        if not messages:
            return 0

        sent = 0
        client = aiosmtplib.SMTP(
            hostname=self.settings.MAIL_SERVER,
            port=self.settings.MAIL_PORT,
            start_tls=self.settings.MAIL_USE_TLS,
        )
        try:
            await client.connect()
            if self.settings.MAIL_USERNAME:
                await client.login(self.settings.MAIL_USERNAME, self.settings.MAIL_PASSWORD)
        except Exception as e:
            logger.error(f"Batch email: SMTP connection failed: {type(e).__name__}")
            return 0

        try:
            for index, item in enumerate(messages):
                try:
                    message = self._build_message(
                        to=item["to"],
                        subject=item["subject"],
                        html_body=item["html_body"],
                        text_body=item.get("text_body"),
                        attachment_path=item.get("attachment_path"),
                    )
                    await client.send_message(
                        message, recipients=[item["to"], *(item.get("bcc") or [])]
                    )
                    sent += 1
                    if index + 1 < len(messages):
                        await asyncio.sleep(0.2)
                except Exception as e:
                    logger.error(
                        f"Batch email: failed for {mask_email(item.get('to', ''))}: "
                        f"{type(e).__name__}"
                    )
        finally:
            try:
                await client.quit()
            except Exception:
                pass

        logger.info(f"Batch email: sent {sent}/{len(messages)}")
        return sent

    async def _attach_file(self, message: MIMEMultipart, file_path: Path) -> None:
        """Attach a file to the email."""
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            # Let the email package quote/encode the name; interpolating it into the header by hand would let
            # a space or a quote in a file name split or terminate the parameter.
            part.add_header("Content-Disposition", "attachment", filename=file_path.name)
            message.attach(part)

    def build_blood_request_notification(
        self,
        donor_email: str,
        donor_name: str,
        blood_group: str,
        patient_name: str,
        hospital_name: str,
        hospital_address: str,
        contact_number: Optional[str],
        due_date: str,
        attendant_name: str,
        units_required: int,
        request_reason: str,
        patient_age: int,
    ) -> dict:
        """Build one donor's notification message (for send_many)."""
        subject = "Urgent Blood Donation Request"

        # Escape all user-controlled values before HTML interpolation
        donor_name, blood_group, patient_name, hospital_name = (
            _esc(str(v)) for v in (donor_name, blood_group, patient_name, hospital_name)
        )
        hospital_address, due_date = _esc(str(hospital_address)), _esc(str(due_date))
        contact_row = ""
        if contact_number:
            contact_row = (
                '<tr><td style="padding: 5px; font-weight: bold;">Attendant Contact:</td>'
                f'<td style="padding: 5px;">{_esc(str(contact_number))}</td></tr>'
            )
        attendant_name = _esc(str(attendant_name))
        units_required = _esc(str(units_required))

        html_body = f"""
        <html>
            <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <table align="center" width="600" style="margin: 20px auto; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td style="background-color: #8B0000; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: bold;">Urgent Blood Donation Request</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; color: #333;">
                            <p style="font-size: 18px; margin: 0 0 15px;">Dear {donor_name},</p>
                            <p style="font-size: 16px; margin: 0 0 20px; line-height: 1.6;">
                                We have identified a new blood donation request that matches your blood type: 
                                <strong style="color: #8B0000;">{blood_group}</strong>.
                            </p>
                            <p style="font-size: 16px; margin: 0 0 15px; font-weight: bold;">Request Details:</p>
                            <table style="width: 100%; font-size: 16px; color: #333; margin-bottom: 20px;">
                                <tr><td style="padding: 5px; font-weight: bold;">Patient Name:</td><td style="padding: 5px;">{patient_name}</td></tr>
                                <tr><td style="padding: 5px; font-weight: bold;">Blood Group Needed:</td><td style="padding: 5px;">{blood_group}</td></tr>
                                <tr><td style="padding: 5px; font-weight: bold;">Units Required:</td><td style="padding: 5px;">{units_required}</td></tr>
                                <tr><td style="padding: 5px; font-weight: bold;">Hospital Name:</td><td style="padding: 5px;">{hospital_name}</td></tr>
                                <tr><td style="padding: 5px; font-weight: bold;">Hospital Address:</td><td style="padding: 5px;">{hospital_address}</td></tr>
                                {contact_row}
                                <tr><td style="padding: 5px; font-weight: bold;">Attendant Name:</td><td style="padding: 5px;">{attendant_name}</td></tr>
                                <tr><td style="padding: 5px; font-weight: bold;">Due Date:</td><td style="padding: 5px;">{due_date}</td></tr>
                            </table>
                            <p style="font-size: 16px; margin: 0 0 20px; line-height: 1.6;">
                                If you are willing and available to donate, please contact us or the attendant directly.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px; text-align: center; background-color: #f8f9fa; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; font-size: 14px; color: #555;">
                            <p style="margin: 0;">
                                Best regards,<br>
                                <strong>LifeConnect Team</strong>
                            </p>
                            <p style="margin: 10px 0 0; font-size: 12px; color: #888;">
                                <strong>Email:</strong> yrclifeconnect@gmail.com
                            </p>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        return {"to": donor_email, "subject": subject, "html_body": html_body}

    async def send_blood_request_notification(self, **kwargs) -> bool:
        """Send a single donor notification (kept for direct callers/tests)."""
        message = self.build_blood_request_notification(**kwargs)
        return await self.send_email(
            to=message["to"], subject=message["subject"], html_body=message["html_body"]
        )

    async def send_otp_email(self, email: str, otp: str, name: str, purpose: str = "password_reset") -> bool:
        """Send an OTP email with copy specific to its security purpose."""
        invite = purpose == "admin_invite"
        title = "Admin invitation code" if invite else "Password reset code"
        subject = f"LifeConnect - {title}"
        name, otp = _esc(str(name)), _esc(str(otp))

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #8B0000; margin-bottom: 20px;">{title}</h2>
                    <p>Dear {name},</p>
                    <p>Your {title.lower()} is:</p>
                    <h1 style="color: #8B0000; font-size: 36px; letter-spacing: 5px; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">{otp}</h1>
                    <p>This OTP is valid for 10 minutes.</p>
                    <p style="color: #888; font-size: 12px; margin-top: 30px;">
                        If you did not request this, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """

        return await self.send_email(to=email, subject=subject, html_body=html_body)

    async def send_certificate_email(
        self, email: str, name: str, certificate_path: Path
    ) -> bool:
        """Send donation certificate to donor."""
        subject = "LifeConnect - Blood Donation Certificate"
        name = _esc(str(name))

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #8B0000; margin-bottom: 20px;">Thank You for Your Donation!</h2>
                    <p>Dear {name},</p>
                    <p>Thank you for your generous blood donation. Your contribution helps save lives.</p>
                    <p>Please find your donation certificate attached to this email.</p>
                    <p style="margin-top: 30px;">
                        Best regards,<br>
                        <strong>LifeConnect Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """

        return await self.send_email(
            to=email,
            subject=subject,
            html_body=html_body,
            attachment_path=certificate_path,
        )

    async def notify_admins_new_request(
        self, admin_emails: List[str], request_details: dict
    ) -> None:
        """
        Tell the active admins about a new blood request with ONE email (BCC), not one per admin.

        The public request form triggers this, so the cost of a submission must not scale with the
        number of admins: one SMTP session per request, to at most ADMIN_NOTIFY_MAX_RECIPIENTS addresses.
        """
        subject = "New Blood Request Submitted"
        request_details = {k: _esc(str(v)) for k, v in request_details.items()}

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>New Blood Request</h2>
                <p>A new blood request has been submitted:</p>
                <ul>
                    <li><strong>Patient:</strong> {request_details.get('patient_name')}</li>
                    <li><strong>Blood Group:</strong> {request_details.get('blood_group')}</li>
                    <li><strong>Hospital:</strong> {request_details.get('hospital_name')}</li>
                    <li><strong>Units:</strong> {request_details.get('units_required')}</li>
                    <li><strong>Due Date:</strong> {request_details.get('due_date')}</li>
                </ul>
                <p>Please review and approve/decline the request.</p>
            </body>
        </html>
        """

        cap = self.settings.ADMIN_NOTIFY_MAX_RECIPIENTS
        recipients = list(dict.fromkeys(admin_emails))
        if len(recipients) > cap:
            logger.warning(
                f"{len(recipients)} active admins but ADMIN_NOTIFY_MAX_RECIPIENTS={cap}: "
                f"notifying the first {cap} only"
            )
            recipients = recipients[:cap]
        if not recipients:
            return

        # To: the sending address itself, so the admins only ever appear in the (invisible) envelope.
        await self.send_many([{
            "to": self.settings.MAIL_FROM,
            "subject": subject,
            "html_body": html_body,
            "bcc": recipients,
        }])

    async def send_certificate(
        self,
        donor_name: str,
        donor_email: str,
        certificate_path: str,
    ) -> bool:
        """
        Send donation certificate to donor (convenience method).
        
        This is a wrapper around send_certificate_email that works with
        the certificate API.
        """
        from pathlib import Path
        return await self.send_certificate_email(
            email=donor_email,
            name=donor_name,
            certificate_path=Path(certificate_path),
        )


# Global service instance
_email_service: EmailService = None


def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        from app.config import get_settings
        settings = get_settings()
        _email_service = EmailService(settings)
    return _email_service

