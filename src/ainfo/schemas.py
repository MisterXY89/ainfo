from __future__ import annotations

"""Pydantic models describing structured extraction outputs."""

from pydantic import BaseModel, Field


class ContactDetails(BaseModel):
    """Standardised contact information extracted from a page."""

    emails: list[str] = Field(default_factory=list, description="Email addresses found in the document.")
    phone_numbers: list[str] = Field(default_factory=list, description="Phone numbers detected in the document.")
    addresses: list[str] = Field(default_factory=list, description="Street addresses discovered in the document.")
    social_media: list[str] = Field(
        default_factory=list,
        description="Social media profile URLs or handles extracted from the document.",
    )


__all__ = ["ContactDetails"]
