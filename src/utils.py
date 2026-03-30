def filter_none_values(d: dict) -> dict:
    """
    Return a new dictionary with all key-value pairs from d where the value is not None or "null".

    Args:
        d (dict): The input dictionary.

    Returns:
        dict: A new dictionary with None and "null" values removed.
    """
    return {k: v for k, v in d.items() if v is not None and v != "null"}
