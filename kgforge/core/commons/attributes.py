from typing import Any


def safe_setattr(object: Any, name: str, value: Any) -> None:
    if hasattr(object, name):
        raise NotImplementedError(f"Name of the property reserved: {name}")
    else:
        setattr(object, name, value)


# FIXME FIXME FIXME

def should_be_overridden():
    raise NotImplementedError("Method should be overridden in the derived classes.")


# FIXME FIXME FIXME

def not_supported(feature: str, object: str) -> None:
    print(f"<not implemented> {feature} is not supported by {object}")
