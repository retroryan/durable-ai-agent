# Tool Validation Guide

## Overview

This project uses a simple, explicit validation pattern for tool arguments. We chose this approach over more complex solutions (like Pydantic or DSPy's type safety) because:

1. **Simplicity** - Easy to understand and maintain
2. **Explicit** - Clear what's being validated
3. **Sufficient** - Handles our validation needs without extra complexity
4. **No dependencies** - Just Python standard library

## Basic Pattern

```python
from typing import Dict, Any
from .validators import validate_args, required_string, optional_int

def my_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define what arguments we expect
    validators = [
        required_string("name"),
        optional_int("count", default=1, min_value=0)
    ]
    
    # Validate and get clean data
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated
    
    # Use the validated values
    name = validated["name"]
    count = validated["count"]
    
    # Tool logic here...
```

## Common Validators

- `required_string(name)` - Required text field
- `optional_string(name, default="")` - Optional text with default
- `required_int(name, min_value=0)` - Required number with minimum
- `optional_int(name, default=0)` - Optional number with default
- `required_date(name)` - Required date (multiple formats supported)
- `required_email(name)` - Required email address

## Why Not Pydantic/DSPy Type Safety?

We evaluated using DSPy's native Pydantic support but decided against it because:

1. **Overkill for simple validation** - Our needs are basic (int >= 0, non-empty strings)
2. **Added complexity** - Would require learning Pydantic for minimal benefit
3. **Current pattern works** - 30+ tests pass with the simple approach
4. **DSPy's strength is elsewhere** - Best for LLM output validation, not input validation

Use Pydantic/DSPy when you need:
- Complex nested data structures
- LLM output validation
- Type safety across system boundaries

Use our simple validators when you need:
- Basic input validation
- Clear, explicit checks
- Minimal dependencies

## Examples

See `example_validations.py` for more validation patterns.