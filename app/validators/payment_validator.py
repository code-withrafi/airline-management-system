import re

from datetime import date


_CARD_RE = re.compile(r"^[0-9]{13,19}$")
_EXPIRY_RE = re.compile(r"^(0[1-9]|1[0-2])\/([0-9]{2})$")
_CVV_RE = re.compile(r"^[0-9]{3,4}$")


class PaymentValidationError(ValueError):
    """
    Raised when payment input fails format validation.
    """
    pass


def validate_card_number(value: str) -> str:

    if not isinstance(value, str):

        raise PaymentValidationError(
            "Card number must be text."
        )

    normalized = (
        value
        .replace(" ", "")
        .replace("-", "")
        .strip()
    )

    if not _CARD_RE.match(normalized):

        raise PaymentValidationError(
            "Card number must be 13 to 19 digits."
        )

    return normalized


def validate_expiry(value: str) -> str:

    if not isinstance(value, str):

        raise PaymentValidationError(
            "Expiry must be text."
        )

    normalized = value.strip()

    match = _EXPIRY_RE.match(normalized)

    if match is None:

        raise PaymentValidationError(
            "Expiry must be in MM/YY format."
        )

    month = int(match.group(1))
    year = int(match.group(2)) + 2000

    today = date.today()

    if (year, month) < (today.year, today.month):

        raise PaymentValidationError(
            "Card has expired."
        )

    return normalized


def validate_cvv(value: str) -> str:

    if not isinstance(value, str):

        raise PaymentValidationError(
            "CVV must be text."
        )

    normalized = value.strip()

    if not _CVV_RE.match(normalized):

        raise PaymentValidationError(
            "CVV must be 3 or 4 digits."
        )

    return normalized


def validate_cardholder(value: str) -> str:

    if not isinstance(value, str):

        raise PaymentValidationError(
            "Cardholder name must be text."
        )

    normalized = value.strip()

    if len(normalized) < 2:

        raise PaymentValidationError(
            "Cardholder name is too short."
        )

    if len(normalized) > 100:

        raise PaymentValidationError(
            "Cardholder name must not exceed 100 characters."
        )

    return normalized
