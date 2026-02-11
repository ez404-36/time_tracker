def remove_spaces(value: str | None) -> str | None:
    return value and value.replace(' ', ' ').replace('‎', '').strip()
