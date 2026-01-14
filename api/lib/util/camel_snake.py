import re

# match:
#   Any uppercase character that is not at the start of a line
#   Any Number that is preceded by a Upper or Lower case character
_REG_TO_SNAKE = re.compile(
    r"(?<!^)(?=[A-Z])|(?<=[A-zA-Z])(?=[0-9])"
)  # re.compile(r"(?<!^)(?=[A-Z])")
_REG_LETTER_AFTER_NUMBER = re.compile(r"(?<=\d)(?=[a-zA-Z])")


def camel_to_snake(name: str) -> str:
    """Converts CamelCase to snake_case

    Args:
        name (str): CamelCase string

    Returns:
        str: snake_case string

    Note:
        This method is preferred over the `to_snake_case` method when converting CamelCase strings.
        It does a better job of handling leading caps. ``UICamelCase`` will be converted to ``ui_camel_case`` and not ``u_i_camel_case``.
    """
    # This function uses regular expressions to insert underscores between the lowercase and uppercase letters, then converts the entire string to lowercase.

    # The first `re.sub` call inserts an underscore before any uppercase letter that is preceded by a lowercase letter or a number.
    # The second `re.sub` call inserts an underscore before any uppercase letter that is followed by a lowercase letter.
    # The `lower` method then converts the entire string to lowercase.
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def to_camel_case(s: str) -> str:
    """
    Converts string to ``CamelCase``

    Args:
        s (str): string to convert such as ``snake_case_word`` or ``pascalCaseWord``

    Returns:
        str: string converted to ``CamelCaseWord``
    """
    s = s.strip()
    if not s:
        return ""
    result = s
    if "_" in result:
        return "".join(word.title() for word in result.split("_"))
    return result[:1].upper() + result[1:]


def to_pascal_case(s: str) -> str:
    """
    Converts string to ``pascalCase``

    Args:
        s (str): string to convert such as ``snake_case_word`` or  ``CamelCaseWord``

    Returns:
        str: string converted to ``pascalCaseWord``
    """
    result = to_camel_case(s)
    if result:
        result = result[:1].lower() + result[1:]
    return result


def to_snake_case(s: str) -> str:
    """
    Convert string to ``snake_case``

    Args:
        s (str): string to convert such as ``pascalCaseWord`` or  ``CamelCaseWord``

    Returns:
        str: string converted to ``snake_case_word``
    """
    s = s.strip()
    if not s:
        return ""
    result = _REG_TO_SNAKE.sub("_", s)
    result = _REG_LETTER_AFTER_NUMBER.sub("_", result)
    return result.lower()


def to_snake_case_upper(s: str) -> str:
    """
    Convert string to ``SNAKE_CASE``

    Args:
        s (str): string to convert such as ``snake_case_word`` or ``pascalCaseWord`` or  ``CamelCaseWord``

    Returns:
        str: string converted to ``SNAKE_CASE_WORD``
    """
    result = to_snake_case(s)
    return result.upper() if s else ""
