"""This module defines the User entity."""

# Natives
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum

# Third-parties
from pydantic import BaseModel, EmailStr, Field, field_validator


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class UserRole(str, Enum):
    DRIVER = "driver"
    OWNER = "owner"


class HistorySummary(BaseModel):
    total_bookings: int = Field(default=0, ge=0)
    no_shows: int = Field(default=0, ge=0)

    @field_validator("no_shows")
    @classmethod
    def validate_no_shows(cls, value: int, info) -> int:
        total_bookings = info.data.get("total_bookings")
        if total_bookings is not None and value > total_bookings:
            raise ValueError("no_shows cannot be greater than total_bookings.")
        return value


class User(BaseModel):
    # Identificador principal del usuario en el sistema/Firebase
    uid: str = Field(min_length=1, max_length=100)

    # Perfil operativo
    display_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    vehicle_plate: str | None = Field(default=None, max_length=20)
    role: UserRole

    # Historial resumido
    history_summary: HistorySummary = Field(default_factory=HistorySummary)

    # Campos heredados del modelo anterior (opcionales para compatibilidad)
    first_name: str | None = Field(default=None, min_length=2, max_length=80)
    last_name: str | None = Field(default=None, min_length=2, max_length=80)
    birth_date: date | None = None
    gender: Gender | None = None
    username: str | None = Field(
        default=None, min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_.-]+$"
    )
    password: str | None = Field(default=None, min_length=8, max_length=128)

    is_active: bool = True

    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str | None) -> str | None:
        if value is None:
            return value

        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_special = any(not c.isalnum() for c in value)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must include at least one uppercase letter, one lowercase letter, one digit, and one special character."
            )
        return value

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date | None) -> date | None:
        if value is None:
            return value

        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise ValueError("User must be at least 13 years old.")
        return value

    @field_validator("vehicle_plate")
    @classmethod
    def validate_vehicle_plate(cls, value: str | None) -> str | None:
        if value is None:
            return value
        plate = value.strip().upper()
        if not plate:
            raise ValueError("vehicle_plate cannot be empty.")
        return plate

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        phone = value.strip()
        if not phone:
            raise ValueError("phone cannot be empty.")
        return phone

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("display_name cannot be empty.")
        return name
