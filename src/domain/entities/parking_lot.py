"""This module defines the ParkingLot entity."""

# Natives
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

# Third-parties
from pydantic import BaseModel, Field, field_validator


class ParkingLotStatus(str, Enum):
    ACTIVE = "active"
    FULL = "full"
    CLOSED = "closed"


class Address(BaseModel):
    street: str = Field(min_length=3, max_length=200)
    reference: str | None = Field(default=None, max_length=250)


class Location(BaseModel):
    geopoint: tuple[float, float] = Field(
        ...,
        description="Latitude and longitude as (lat, lng).",
    )
    geohash: str | None = Field(default=None, min_length=1, max_length=12)

    @field_validator("geopoint")
    @classmethod
    def validate_geopoint(cls, value: tuple[float, float]) -> tuple[float, float]:
        if len(value) != 2:
            raise ValueError("geopoint must contain exactly two values: latitude and longitude.")

        lat, lng = value
        if not (-90.0 <= lat <= 90.0):
            raise ValueError("Latitude must be between -90 and 90.")
        if not (-180.0 <= lng <= 180.0):
            raise ValueError("Longitude must be between -180 and 180.")

        return value


class Pricing(BaseModel):
    hourly_rate: float = Field(gt=0)
    fraction_rate: float = Field(gt=0)

    @field_validator("hourly_rate", "fraction_rate")
    @classmethod
    def validate_money_values(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Pricing values must be greater than 0.")
        return value


class Capacity(BaseModel):
    total_slots: int = Field(ge=0)
    available_slots: int = Field(ge=0)

    @field_validator("available_slots")
    @classmethod
    def validate_available_slots(cls, value: int, info) -> int:
        total_slots = info.data.get("total_slots")
        if total_slots is not None and value > total_slots:
            raise ValueError("available_slots cannot be greater than total_slots.")
        return value


class ParkingLot(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=3, max_length=150)
    owner_id: str = Field(min_length=1, max_length=100)

    address: Address
    location: Location
    pricing: Pricing
    capacity: Capacity

    features: list[str] = Field(default_factory=list)
    status: ParkingLotStatus = ParkingLotStatus.ACTIVE

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: list[str]) -> list[str]:
        normalized = [feature.strip().lower() for feature in value if feature.strip()]
        if len(normalized) != len(set(normalized)):
            raise ValueError("features must not contain duplicated values.")
        return normalized
