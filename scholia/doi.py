"""doi.

Usage:

Options:

References
----------
  https://doi.org

"""

import re

import requests
from flask import current_app

USER_AGENT = "Scholia"

CROSSREF_URL = "https://api.crossref.org/v1/works/"


def get_doi_metadata(doi):
    """Get metadata about a DOI from Crossref API.

    Uses the Crossref API to return the metadata for the paper in a dictionary.

    Parameters
    ----------
    doi : str
        DOI identifier.

    Returns
    -------
    metadata : dict
        Dictionary with metadata.

    Notes
    -----
    Works with raw DOIs and doi.org URLs

    Examples
    --------
    >>> metadata = get_doi_metadata('10.1177/0269216319865414')
    >>> metadata['publication_date'] == '2019-09-05'
    True

    >>> get_doi_metadata('10.1177/123456789')
    {'error': 'Not found'}

    """

    def get_date(date_list):
        if (len(date_list) == 1 and date_list[0] != "None" and
                date_list[0] is not None):
            date = f"{date_list[0]}"
            return date, f"+{date}-00-00T00:00:00Z/9"
        if len(date_list) == 2:
            date = f"{date_list[0]}-{date_list[1]:02d}"
            return date, f"+{date}-00T00:00:00Z/10"
        if len(date_list) == 3:
            date = f"{date_list[0]}-{date_list[1]:02d}-{date_list[2]:02d}"
            return date, f"+{date}T00:00:00Z/11"

        return "", ""

    def get_author_name(author_dict):
        name = author_dict.get('name', '')
        given_name = author_dict.get('given', '')
        family_name = author_dict.get('family', '')
        formatted_name = f"{name} {given_name} {family_name}".strip()
        return formatted_name

    doi = doi.strip()

    url = CROSSREF_URL + doi

    try:
        response = requests.get(url)

        if response.status_code == 200:
            entry = response.json()["message"]

            plain_date, date = get_date(entry["issued"]["date-parts"][0])

            metadata = {
                "doi": entry.get("DOI"),
                "authornames": [
                    get_author_name(author)
                    for author in entry.get("author", [])
                ],
                # not full text url if the paper is closed source
                # "full_text_url":
                #      entry.get("resource", {}).get("primary", {}).get("URL"),
                "publication_date_P577": date,
                "publication_date": plain_date,
                # Some titles may have a newline in them. This should be
                # converted to an ordinary space character
                "title": re.sub(r"\s+", " ", entry["title"][0]),
            }
            return metadata

        else:
            if response.text == "Resource not found.":
                return {'error': "Not found"}
            # Handle non-200 status codes (e.g., 404, 500) appropriately
            status_code = response.status_code
            return {"error": f"Request failed with status code {status_code}"}

    except requests.exceptions.RequestException as e:
        # connection timeout, DNS resolution error, etc
        current_app.logger.debug(f'Request failed due to a network error: {e}')
        return {'error': 'Request failed due to a network error'}

    except Exception as e:
        current_app.logger.debug(f'An unexpected error occurred: {e}')
        return {'error': 'An unexpected error occurred'}


def string_to_doi(string):
    """Extract doi id from string.

    The DOI identifier part of `string` will be extracted. If multiple
    identifier patterns are in the input string then only the first
    is returned.

    Parameters
    ----------
    string : str
        String with doi ID.

    Returns
    -------
    doi : str or None
        String with doi ID.

    Examples
    --------
    >>> string_to_doi('10.1371/JOURNAL.PONE.0029797')
    '10.1371/JOURNAL.PONE.0029797'

    >>> string_to_doi('https://doi.org/10.12987/YALE/9780300197051.003.0010')
    '10.12987/YALE/9780300197051.003.0010'

    >>> string_to_doi('https://doi.org/10') is None
    True

    """
    PATTERN = re.compile(
        r"(?i)10.\d{4,9}/[^\s]+", flags=re.DOTALL | re.UNICODE
    )
    dois = PATTERN.findall(string)
    if len(dois) > 0:
        return dois[0]
    return None


def main():
    """Handle command-line interface."""
    print("undefined")


if __name__ == "__main__":
    main()