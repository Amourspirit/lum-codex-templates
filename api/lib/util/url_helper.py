from urllib.parse import unquote, quote


def decode_url_component(encoded_str: str) -> str:
    """
    Decodes a URL-encoded string.

    The input string is expected to be URL-encoded, and this function will return the decoded version of it.
    It also trims any leading or trailing whitespace from the input before decoding.

    Args:
        encoded_str (str): The URL-encoded string to decode.

    Returns:
        str: The decoded string.
    """
    return unquote(encoded_str.strip())


def encode_url_component(raw_str: str) -> str:
    """
    Encodes a string into URL-encoded format.

    This function takes a raw string and encodes it using URL encoding, which replaces special characters with their percent-encoded equivalents.
    It also trims any leading or trailing whitespace from the input before encoding.

    Args:
        raw_str (str): The raw string to encode.
    Returns:
        str: The URL-encoded string.
    """
    return quote(raw_str.strip())
