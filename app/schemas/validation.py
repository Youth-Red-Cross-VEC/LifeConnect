"""Shared validation for incoming domain values. Response models also serve legacy rows."""
import re
from datetime import date, datetime
from typing import Annotated, Literal
from unicodedata import category

from pydantic import AfterValidator, BeforeValidator, Field


def _clean_text(value: object, *, multiline: bool = False) -> object:
    if not isinstance(value, str):
        return value
    allowed_controls = "\t\r\n" if multiline else ""
    if any(category(c) == "Cc" and c not in allowed_controls for c in value):
        raise ValueError("Text contains unsupported control characters")
    return value.strip()


def _paragraph(value: object) -> object:
    return _clean_text(value, multiline=True)


def _phone(value: object) -> object:
    if not isinstance(value, str):
        return value
    if len(value) > 48 or not re.fullmatch(r"[+0-9 ()-]+", value):
        raise ValueError("Use a phone number with 10 to 15 digits and an optional leading +")
    digits = re.sub(r"[ ()-]", "", value)
    if not re.fullmatch(r"\+?[0-9]{10,15}", digits):
        raise ValueError("Use a phone number with 10 to 15 digits and an optional leading +")
    return digits


def _group(value: object) -> object:
    return value.strip().upper() if isinstance(value, str) else value


def _calendar_input(value: object) -> date | str:
    if isinstance(value, date) or (isinstance(value, str) and re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}", value)):
        return value
    raise ValueError("Use an ISO calendar date, for example 2000-01-31")


def _quantity(value: object) -> object:
    if isinstance(value, bool):
        raise ValueError("Use a whole number")
    return value


def _birth_date(value: date) -> date:
    if value > date.today():
        raise ValueError("Date of birth cannot be in the future")
    return value


OtpCode = Annotated[str, Field(pattern=r"^[0-9]{6}$")]
SingleLine = Annotated[str, BeforeValidator(_clean_text)]
Paragraph = Annotated[str, BeforeValidator(_paragraph)]
Phone = Annotated[str, Field(pattern=r"^\+?[0-9]{10,15}$"), BeforeValidator(_phone)]
BloodGroup = Annotated[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], BeforeValidator(_group)]
PostalCode = Annotated[str, Field(min_length=5, max_length=10, pattern=r"^[A-Za-z0-9]+(?:[ -][A-Za-z0-9]+)*$"), BeforeValidator(_clean_text)]
CalendarDate = Annotated[date, BeforeValidator(_calendar_input)]
CalendarDateTime = Annotated[datetime, BeforeValidator(_calendar_input)]
BirthDate = Annotated[CalendarDate, AfterValidator(_birth_date)]
Quantity = Annotated[int, BeforeValidator(_quantity)]
RecordId = Annotated[str, Field(min_length=1, max_length=36, pattern=r"^[^\s/,\\]+$"), BeforeValidator(_clean_text)]
