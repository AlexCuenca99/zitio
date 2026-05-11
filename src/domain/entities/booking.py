"""This module defines the Booking entity."""

# Natives
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

# Third-parties
from pydantic import BaseModel, Field, field_validator


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingTimestamps(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, value: datetime, info) -> datetime:
        created_at = info.data.get("created_at")
        if created_at is not None and value <= created_at:
            raise ValueError("expires_at must be later than created_at.")
        return value

    @field_validator("checked_in_at")
    @classmethod
    def validate_checked_in_at(cls, value: datetime | None, info) -> datetime | None:
        created_at = info.data.get("created_at")
        expires_at = info.data.get("expires_at")

        if value is None:
            return value

        if created_at is not None and value < created_at:
            raise ValueError("checked_in_at cannot be earlier than created_at.")
        if expires_at is not None and value > expires_at:
            raise ValueError("checked_in_at cannot be later than expires_at.")

        return value

    @field_validator("checked_out_at")
    @classmethod
    def validate_checked_out_at(cls, value: datetime | None, info) -> datetime | None:
        checked_in_at = info.data.get("checked_in_at")

        if value is None:
            return value

        if checked_in_at is not None and value < checked_in_at:
            raise ValueError("checked_out_at cannot be earlier than checked_in_at.")

        return value


class Booking(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    user_id: str = Field(min_length=1, max_length=100)
    parking_id: str = Field(min_length=1, max_length=100)

    status: BookingStatus = BookingStatus.PENDING
    timestamps: BookingTimestamps

    total_price: float = Field(default=0.0, ge=0)
    qr_code_token: str = Field(min_length=16, max_length=255)

    @field_validator("total_price")
    @classmethod
    def validate_total_price(cls, value: float) -> float:
        if value < 0:
            raise ValueError("total_price cannot be negative.")
        return value

    @field_validator("qr_code_token")
    @classmethod
    def validate_qr_code_token(cls, value: str) -> str:
        token = value.strip()
        if not token:
            raise ValueError("qr_code_token cannot be empty.")
        return token
