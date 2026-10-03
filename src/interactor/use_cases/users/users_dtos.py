"""This module defines the client input accepted to create and update a user profile."""

from pydantic import BaseModel, ConfigDict


class UserProfileCreate(BaseModel):
    """Fields a client may send to create its profile.

    uid and email come from the verified token and role always starts as driver, so any
    other field is rejected instead of silently ignored. Field constraints are enforced by
    the User entity the use case builds from this input.
    """

    model_config = ConfigDict(extra="forbid")

    display_name: str
    phone: str | None = None
    vehicle_plate: str | None = None


class UserProfileUpdate(BaseModel):
    """Fields a client may change in its profile; every other field is rejected."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    phone: str | None = None
    vehicle_plate: str | None = None
