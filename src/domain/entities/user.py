"""This module defines the User entity: the Zitio profile linked to a Firebase account."""

# Natives
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum

# Third-parties
from pydantic import BaseModel, EmailStr, Field, field_validator


class Gender(str, Enum):
    """Gender a user may declare."""

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class UserRole(str, Enum):
    """Role of a user: drivers book slots, owners publish parking lots."""

    DRIVER = "driver"
    OWNER = "owner"


class HistorySummary(BaseModel):
    """Booking counters of a user."""

    total_bookings: int = Field(default=0, ge=0)
    no_shows: int = Field(default=0, ge=0)

    @field_validator("no_shows")
    @classmethod
    def validate_no_shows(cls, value: int, info) -> int:
        """Check that no-shows never exceed the total bookings.

        Args:
            value: Number of no-shows.
            info: Validation info with the fields validated so far.

        Returns:
            The number of no-shows.

        Raises:
            ValueError: If no_shows is greater than total_bookings.
        """
        total_bookings = info.data.get("total_bookings")
        if total_bookings is not None and value > total_bookings:
            raise ValueError("no_shows cannot be greater than total_bookings.")
        return value


class User(BaseModel):
    """Zitio profile of a user. Credentials live in Firebase Auth, never here."""

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

    is_active: bool = True

    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date | None) -> date | None:
        """Check that the user is at least 13 years old.

        Args:
            value: Date of birth, if given.

        Returns:
            The date of birth.

        Raises:
            ValueError: If the user is younger than 13.
        """
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
        """Normalize the vehicle plate to uppercase without surrounding spaces.

        Args:
            value: Vehicle plate, if given.

        Returns:
            The normalized plate.

        Raises:
            ValueError: If the plate is blank.
        """
        if value is None:
            return value
        plate = value.strip().upper()
        if not plate:
            raise ValueError("vehicle_plate cannot be empty.")
        return plate

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Strip surrounding spaces from the phone.

        Args:
            value: Phone number, if given.

        Returns:
            The stripped phone number.

        Raises:
            ValueError: If the phone is blank.
        """
        if value is None:
            return value
        phone = value.strip()
        if not phone:
            raise ValueError("phone cannot be empty.")
        return phone

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        """Strip surrounding spaces from the display name.

        Args:
            value: Display name.

        Returns:
            The stripped display name.

        Raises:
            ValueError: If the display name is blank.
        """
        name = value.strip()
        if not name:
            raise ValueError("display_name cannot be empty.")
        return name
