"""Email address handling shared by every lookup and write."""


def normalize_email(email: str) -> str:
    """The canonical stored/compared form: trimmed and lowercase.

    EmailStr only lowercases the domain; the local part keeps its case, so "Pat@x.com" and "pat@x.com"
    would otherwise be two accounts (and two inboxes worth of password-reset codes) for one person.
    """
    return email.strip().lower()
