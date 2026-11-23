import httpx
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

MINIMUM_SCORE = 0.5  # reCAPTCHA v3 score threshold (0.0 bot → 1.0 human)

async def verify_recaptcha(token: str, action: str | None = None) -> bool:
    """
    Verify a reCAPTCHA v3 token with Google's API.

    Args:
        token: The reCAPTCHA token returned by the client.
        action: Expected action name (e.g. "login"). Checked when provided.

    Returns:
        True if the token is valid and the risk score >= MINIMUM_SCORE.
        False on verification failure, low score, or request errors.
    """
    settings = get_settings()
    secret_key = settings.RECAPTCHA_SECRET_KEY
    if not secret_key:
        if settings.APP_ENV.lower() == "development":
            logger.warning("RECAPTCHA_SECRET_KEY is not set — skipping verification (development only)")
            return True
        logger.error("RECAPTCHA_SECRET_KEY is not set — rejecting request (fail closed)")
        return False

    url = "https://www.google.com/recaptcha/api/siteverify"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                data={
                    "secret": secret_key,
                    "response": token,
                }
            )
            response.raise_for_status()
            result = response.json()

        if not result.get("success", False):
            logger.warning("reCAPTCHA verification rejected")
            return False

        score: float = result.get("score", 0.0)
        returned_action: str = result.get("action", "")

        if action and returned_action != action:
            logger.warning(
                "reCAPTCHA action mismatch"
            )
            return False

        if score < MINIMUM_SCORE:
            logger.warning(
                "reCAPTCHA v3 score too low: %.2f (minimum %.2f)",
                score, MINIMUM_SCORE
            )
            return False

        logger.info("reCAPTCHA v3 passed — score: %.2f, action: %s", score, action)
        return True

    except Exception as e:
        logger.error("Error verifying reCAPTCHA: %s", type(e).__name__)
        return False
