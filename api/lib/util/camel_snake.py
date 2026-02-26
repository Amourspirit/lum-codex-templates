from src.util import camel_snake


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
    return camel_snake.camel_to_snake(name)


def to_camel_case(s: str) -> str:
    """
    Converts string to ``CamelCase``

    Args:
        s (str): string to convert such as ``snake_case_word`` or ``pascalCaseWord``

    Returns:
        str: string converted to ``CamelCaseWord``
    """
    return camel_snake.to_camel_case(s)


def to_pascal_case(s: str) -> str:
    """
    Converts string to ``pascalCase``

    Args:
        s (str): string to convert such as ``snake_case_word`` or  ``CamelCaseWord``

    Returns:
        str: string converted to ``pascalCaseWord``
    """
    return camel_snake.to_pascal_case(s)


def to_snake_case(s: str) -> str:
    """
    Convert string to ``snake_case``

    Args:
        s (str): string to convert such as ``pascalCaseWord`` or  ``CamelCaseWord``

    Returns:
        str: string converted to ``snake_case_word``
    """
    return camel_snake.to_snake_case(s)


def to_snake_case_upper(s: str) -> str:
    """
    Convert string to ``SNAKE_CASE``

    Args:
        s (str): string to convert such as ``snake_case_word`` or ``pascalCaseWord`` or  ``CamelCaseWord``

    Returns:
        str: string converted to ``SNAKE_CASE_WORD``
    """
    return camel_snake.to_snake_case(s).upper()
