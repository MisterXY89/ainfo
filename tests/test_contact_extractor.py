"""Tests for contact information extraction helpers."""

from ainfo.extractors.contact import (
    extract_addresses,
    extract_emails,
    extract_phone_numbers,
)


def test_extract_emails() -> None:
    """Emails are detected and deduplicated."""
    text = (
        "Email us at first@example.com and second@example.com; "
        "first@example.com again."
    )
    assert extract_emails(text) == [
        "first@example.com",
        "second@example.com",
    ]


def test_extract_phone_numbers() -> None:
    """Phone numbers are normalized to digits when phonenumbers is absent."""
    text = "Call (123) 456-7890 or 987-654-3210."
    assert extract_phone_numbers(text) == [
        "1234567890",
        "9876543210",
    ]


def test_extract_addresses() -> None:
    """Street addresses are extracted in order."""
    text = "Locations: 123 Main St., 456 Elm Road"
    assert extract_addresses(text) == [
        "123 Main St",
        "456 Elm Road",
    ]
