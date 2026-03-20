# Centralized input validators for Go-onCare
# Provides both real-time QValidator subclasses and helper functions
# for submit-time (accept()) validation.

import re
from PyQt6.QtGui import QValidator, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression


# ══════════════════════════════════════════════════════════════════════
#  Real-time QValidator subclasses (attach to QLineEdit via setValidator)
# ══════════════════════════════════════════════════════════════════════

class NameValidator(QValidator):
    """Allows letters, spaces, hyphens, periods, and apostrophes only.
    Rejects pure digits or strings starting with a digit."""

    def validate(self, text, pos):
        if not text:
            return QValidator.State.Intermediate, text, pos
        # Allow only letters (incl. accented), spaces, hyphens, dots, apostrophes
        if re.match(r"^[A-Za-zÀ-ÿ\s\.\-\'']+$", text):
            return QValidator.State.Acceptable, text, pos
        return QValidator.State.Invalid, text, pos


class PhoneDigitsValidator(QValidator):
    """Allows only digits, max 10 characters (for PH mobile after +63)."""

    def validate(self, text, pos):
        if not text:
            return QValidator.State.Intermediate, text, pos
        if text.isdigit() and len(text) <= 10:
            return QValidator.State.Acceptable, text, pos
        if text.isdigit():
            return QValidator.State.Invalid, text, pos
        return QValidator.State.Invalid, text, pos


class PriceValidator(QValidator):
    """Allows digits and at most one decimal point. For price text fields."""

    def validate(self, text, pos):
        if not text:
            return QValidator.State.Intermediate, text, pos
        if re.match(r'^\d+\.?\d{0,2}$', text):
            return QValidator.State.Acceptable, text, pos
        # Allow partial typing like "123." (no digits after dot yet)
        if re.match(r'^\d+\.$', text):
            return QValidator.State.Intermediate, text, pos
        return QValidator.State.Invalid, text, pos


# ══════════════════════════════════════════════════════════════════════
#  Submit-time validation helpers (for use in accept() overrides)
# ══════════════════════════════════════════════════════════════════════

_EMAIL_RE = re.compile(r'^[\w.+-]+@[\w-]+\.[\w.]+$')


def validate_required(value: str, field_name: str) -> str | None:
    """Return error message if value is empty/whitespace, else None."""
    if not value.strip():
        return f"{field_name} is required."
    return None


def validate_name(value: str, field_name: str = "Name") -> str | None:
    """Return error message if name contains digits or is too short."""
    text = value.strip()
    if not text:
        return f"{field_name} is required."
    if len(text) < 2:
        return f"{field_name} must be at least 2 characters."
    if not re.match(r"^[A-Za-zÀ-ÿ\s\.\-\'']+$", text):
        return f"{field_name} should contain only letters, spaces, hyphens, and periods."
    return None


def validate_email(value: str) -> str | None:
    """Return error message if email format is invalid, else None."""
    text = value.strip()
    if not text:
        return None  # Email may be optional; caller checks required separately
    if not _EMAIL_RE.match(text):
        return "Please enter a valid email address (e.g. name@example.com)."
    return None


def validate_phone_digits(value: str) -> str | None:
    """Return error message if not exactly 10 digits."""
    text = value.strip()
    if not text:
        return None  # Caller checks required separately
    if not re.match(r'^\d{10}$', text):
        return "Enter exactly 10 digits after +63 (e.g. 9171234567)."
    return None


def validate_price(value: str, field_name: str = "Price") -> str | None:
    """Return error message if not a valid positive number."""
    text = value.strip().replace("₱", "").replace(",", "")
    if not text:
        return f"{field_name} is required."
    try:
        p = float(text)
        if p < 0:
            return f"{field_name} cannot be negative."
    except ValueError:
        return f"{field_name} must be a valid number."
    return None
