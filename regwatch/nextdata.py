"""Decode the observed public Next flight JSON listing without running JavaScript."""
import json
import re

from bs4 import BeautifulSoup


def extract_next_rows(body, path):
    """Find an exact dot path within a JSON flight payload; fail on shape drift."""
    decoder = json.JSONDecoder()
    found = []
    for script in BeautifulSoup(body, 'html.parser').find_all('script'):
        text = script.get_text()
        for match in re.finditer(r'self\.__next_f\.push\s*\(', text):
            try:
                frame, _ = decoder.raw_decode(text[match.end():].lstrip())
                if not isinstance(frame, list) or len(frame) != 2 or frame[0] != 1 or not isinstance(frame[1], str):
                    continue
                _, separator, payload = frame[1].partition(':')
                if not separator:
                    continue
                value = json.loads(payload)
                for segment in path.split('.'):
                    value = value[int(segment)] if isinstance(value, list) and segment.isdigit() else value[segment]
            except (ValueError, TypeError, KeyError, IndexError):
                continue
            if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
                raise ValueError('Next flight listing has an invalid row shape')
            found.append(value)
    if len(found) != 1:
        raise ValueError('Expected exactly one Next flight listing at ' + path)
    return found[0]
