''' MathML Escape Codes

Python's XML parser doesn't like these, so they must be replaced
before parsing.
'''

import re
from . import escape_codes

ESCAPES = escape_codes.ESCAPES
ESCAPES.update({
    '-': '−',   # Real minus, not hyphen
    ':=': '≔',
    r'\*=': '⩮',  # NOTE: * is escaped for use in re
    '==': '⩵',
    '!=': '≠',
    '&InvisibleComma;': '',
    '&InvisibleTimes;': '',
    # These are picked up by XML parser already
    # '&lt;' : '<',
    # '&gt;' : '>',
    # '&amp;': '&',
    })

regex = re.compile('|'.join(map(re.escape, ESCAPES.keys())))


def unescape(xmlstr: str) -> str:
    ''' Remove MathML escape codes from xml string '''
    return regex.sub(lambda match: ESCAPES[match.group(0)], xmlstr)
