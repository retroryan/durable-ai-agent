"""
Pydantic models for MCP server request validation.

These models provide automatic type coercion and validation for tool inputs,
specifically handling the case where AWS Bedrock passes coordinates as strings.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class LocationInput(BaseModel):
    """
    Base model for location and coordinate inputs with automatic type coercion.

    This model handles the common case where AWS Bedrock passes coordinates
    as strings (e.g., "41.8781") instead of floats. Pydantic automatically
    converts these to the correct type.
    """

    location: Optional[str] = Field(
        None,
        description="Location name (e.g., 'Chicago, IL'). Slower due to geocoding.",
    )
    latitude: Optional[float] = Field(
        None, description="Direct latitude (-90 to 90). PREFERRED for faster response."
    )
    longitude: Optional[float] = Field(
        None,
        description="Direct longitude (-180 to 180). PREFERRED for faster response.",
    )

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude is within valid range."""
        if v is not None:
            # Handle string input that might have extra characters
            if isinstance(v, str):
                # Remove any quotes or extra characters
                v = v.strip("\"'")
                try:
                    v = float(v)
                except ValueError:
                    raise ValueError(f"Invalid latitude format: {v}")

            if not -90 <= v <= 90:
                raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude is within valid range."""
        if v is not None:
            # Handle string input that might have extra characters
            if isinstance(v, str):
                # Remove any quotes or extra characters
                v = v.strip("\"'")
                try:
                    v = float(v)
                except ValueError:
                    raise ValueError(f"Invalid longitude format: {v}")

            if not -180 <= v <= 180:
                raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v

    @model_validator(mode="after")
    def check_at_least_one_location(self):
        """Ensure at least one location method is provided."""
        has_location = self.location is not None
        has_coords = self.latitude is not None and self.longitude is not None
        if not has_location and not has_coords:
            raise ValueError(
                "Either location name or coordinates (latitude, longitude) required"
            )
        return self


class ForecastRequest(LocationInput):
    """Request model for weather forecast tool."""

    days: int = Field(
        default=7, ge=1, le=16, description="Number of forecast days (1-16)"
    )


class HistoricalRequest(LocationInput):
    """Request model for historical weather tool."""

    start_date: str = Field(
        ...,
        description="Start date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    end_date: str = Field(
        ..., description="End date in YYYY-MM-DD format", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format and parse to ensure it's valid."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD.")
        return v

    @model_validator(mode="after")
    def validate_date_order(self):
        """Ensure end date is after start date."""
        if self.start_date and self.end_date:
            start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
            end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
            if end < start:
                raise ValueError("End date must be after start date.")
        return self


class AgriculturalRequest(LocationInput):
    """Request model for agricultural conditions tool."""

    days: int = Field(
        default=7, ge=1, le=7, description="Number of forecast days (1-7)"
    )
