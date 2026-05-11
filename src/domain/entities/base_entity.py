"""This module defines the base entity class"""

# Natives
from datetime import datetime
from uuid import UUID

# Third-parties
from pydantic import BaseModel


class BaseEntity(BaseModel):
    id: UUID

    created_at: datetime
