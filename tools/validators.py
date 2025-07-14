from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class ValidationError(Exception):
    """Custom exception for validation errors"""

    pass


class FieldType(Enum):
    """Supported field types for validation"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    ENUM = "enum"


class FieldValidator:
    """Configuration for a single field validation"""

    def __init__(
        self,
        name: str,
        field_type: FieldType,
        required: bool = True,
        default: Any = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        allowed_values: Optional[List[Any]] = None,
        custom_validator: Optional[Callable[[Any], bool]] = None,
        error_message: Optional[str] = None,
    ):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.allowed_values = allowed_values
        self.custom_validator = custom_validator
        self.error_message = error_message


def validate_args(
    args: Dict[str, Any], validators: List[FieldValidator]
) -> Dict[str, Any]:
    """
    Validate and parse arguments according to field validators.

    Args:
        args: Raw arguments dictionary
        validators: List of FieldValidator configurations

    Returns:
        Dict with validated and parsed values

    Raises:
        Returns dict with 'error' key if validation fails
    """
    validated = {}

    for validator in validators:
        raw_value = args.get(validator.name)

        # Handle required fields
        if raw_value is None or raw_value == "":
            if validator.required:
                error_msg = validator.error_message or f"'{validator.name}' is required"
                return {"error": error_msg}
            else:
                validated[validator.name] = validator.default
                continue

        # Type conversion and validation
        try:
            parsed_value = _parse_field(raw_value, validator)

            # Additional validations
            if not _validate_constraints(parsed_value, validator):
                error_msg = (
                    validator.error_message or f"Invalid value for '{validator.name}'"
                )
                return {"error": error_msg}

            validated[validator.name] = parsed_value

        except (ValueError, TypeError) as e:
            error_msg = (
                validator.error_message
                or f"Invalid {validator.field_type.value} for '{validator.name}'"
            )
            return {"error": error_msg}

    return validated


def _parse_field(value: Any, validator: FieldValidator) -> Any:
    """Parse a field value according to its type"""
    if validator.field_type == FieldType.STRING:
        return str(value)

    elif validator.field_type == FieldType.INTEGER:
        # Handle string numbers with fallback
        if isinstance(value, str) and not value.strip():
            value = "0"
        return int(value)

    elif validator.field_type == FieldType.FLOAT:
        if isinstance(value, str) and not value.strip():
            value = "0.0"
        return float(value)

    elif validator.field_type == FieldType.BOOLEAN:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        return bool(value)

    elif validator.field_type == FieldType.DATE:
        if isinstance(value, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Could not parse date: {value}")
        return value

    elif validator.field_type == FieldType.DATETIME:
        if isinstance(value, str):
            # Try common datetime formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Could not parse datetime: {value}")
        return value

    elif validator.field_type == FieldType.EMAIL:
        # Basic email validation
        email_str = str(value)
        if "@" not in email_str or "." not in email_str.split("@")[1]:
            raise ValueError(f"Invalid email format: {email_str}")
        return email_str

    elif validator.field_type == FieldType.ENUM:
        return str(value)

    else:
        return value


def _validate_constraints(value: Any, validator: FieldValidator) -> bool:
    """Validate value against constraints"""
    # Numeric constraints
    if validator.min_value is not None and value < validator.min_value:
        return False
    if validator.max_value is not None and value > validator.max_value:
        return False

    # String length constraints
    if isinstance(value, str):
        if validator.min_length is not None and len(value) < validator.min_length:
            return False
        if validator.max_length is not None and len(value) > validator.max_length:
            return False

    # Enum/allowed values
    if validator.allowed_values is not None and value not in validator.allowed_values:
        return False

    # Custom validation
    if validator.custom_validator is not None and not validator.custom_validator(value):
        return False

    return True


# Convenience functions for common validations
def required_string(name: str, **kwargs) -> FieldValidator:
    """Create a required string field validator"""
    return FieldValidator(name, FieldType.STRING, required=True, **kwargs)


def optional_string(name: str, default: str = "", **kwargs) -> FieldValidator:
    """Create an optional string field validator"""
    return FieldValidator(
        name, FieldType.STRING, required=False, default=default, **kwargs
    )


def required_int(name: str, **kwargs) -> FieldValidator:
    """Create a required integer field validator"""
    return FieldValidator(name, FieldType.INTEGER, required=True, **kwargs)


def optional_int(name: str, default: int = 0, **kwargs) -> FieldValidator:
    """Create an optional integer field validator"""
    return FieldValidator(
        name, FieldType.INTEGER, required=False, default=default, **kwargs
    )


def required_date(name: str, **kwargs) -> FieldValidator:
    """Create a required date field validator"""
    return FieldValidator(name, FieldType.DATE, required=True, **kwargs)


def required_email(name: str, **kwargs) -> FieldValidator:
    """Create a required email field validator"""
    return FieldValidator(name, FieldType.EMAIL, required=True, **kwargs)
