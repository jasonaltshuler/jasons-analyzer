import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def short(string):
    if len(string) <= 100:
        return f"{string}"
    else:
        """Format text with only the first 100 characters."""
        return f"{string[:100]}..."


def thesaurus(word):
    # Get synonyms for frequently used words

    # Contact API
    try:
        api_key = "5fefc6d7da1691177536ec2e9815e16d"
        response = requests.get(f"https://words.bighugelabs.com/api/2/{api_key}/{word}/json")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        thesaurus = response.json()
        return thesaurus
    except (KeyError, TypeError, ValueError):
        return None

def decode(string):
    return string.replace('\\n','\n')\