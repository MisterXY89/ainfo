def extract_information(parsed: dict) -> list:
    """Extract information from the parsed data.

    Parameters
    ----------
    parsed: dict
        Parsed representation of the data.

    Returns
    -------
    list
        A list of extracted elements.
    """
    return list(parsed.values())
