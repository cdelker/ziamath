''' Apply italic, bold, and other font styles by shifting the unstyled ASCII
    characters [A-Z, a-z, and 0-9] to their higher unicode alternatives. Note
    this does not check whether the new character glyph exists in the font.
'''
from typing import Literal

StyleType = Literal['serif', 'sans', 'script', 'fraktur', 'double', 'mono']


def styledchr(c: str, italic: bool=False, bold: bool=False,
              style: StyleType='serif') -> str:
    ''' Convert an ASCII character into it's styled unicode counterpart '''
    ordc = ord(c)
    if not ((0x41 <= ordc <= 0x5A) or (0x61 <= ordc <= 0x7A) or (0x30 <= ordc <= 0x39)):
        return c

    # Look up replacement characters that don't map directly by offset
    # because unicode defines them in a weird place.
    replace = {('serif', True, False): {
                   'h': 'ℎ'},
               ('script', False, False): {
                   'B': 'ℬ', 'E': 'ℰ', 'F': 'ℱ', 'H': 'ℋ', 'I': 'ℐ', 'L': 'ℒ',
                   'M': 'ℳ', 'R': 'ℛ', 'e': 'ℯ', 'g': 'ℊ', 'o': 'ℴ'},
                ('fraktur', False, False): {
                    'C': 'ℭ', 'H': 'ℌ', 'I': 'ℑ', 'R': 'ℜ', 'Z': 'ℨ'},
                ('double', False, False): {
                    'C': 'ℂ', 'H': 'ℍ', 'N': 'ℕ', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'Z': 'ℤ'}}

    cx = replace.get((style, italic, bold), {}).get(c)
    if cx is not None:
        return cx

    if (0x30 <= ordc <= 0x39):  # Digit
        #        style    bold
        ofst = {('serif', True): 0x1D7CE,
                ('double', False): 0x1D7D8,
                ('sans', False): 0x1D7E2,
                ('sans', True): 0x1D7EC,
                ('mono', False): 0x1D7F6}.get((style, bold))
        if ofst is None:
            return c
        return chr(ordc - ord('0') +ofst)

    if (0x61 <= ordc <= 0x7A):
        # Lowercase
        base = ordc - 6 - ord('A')
    else:
        base = ordc - ord('A')

    ofst = None
    if style == 'serif':
        ofst = {(False, True): 0x1D400,
                (True, False): 0x1D434,
                (True, True): 0x1D468}.get((italic, bold))
    elif style == 'sans':
        ofst = {(False, False): 0x1D5A0,
                (False, True): 0x1D5D4,
                (True, False): 0x1D608,
                (True, True): 0x1D63C}.get((italic, bold))
    elif style == 'script':
        ofst = {False: 0x1D49C,
                True: 0x1D4D0}.get(bold)
    elif style == 'fraktur':
        ofst = {False: 0x1D504,
                True: 0x1D504}.get(bold)
    elif style == 'mono':
        ofst = 0x1D670
    elif style == 'double':
        ofst = 0x1D538

    if ofst is None:
        return c

    return chr(base + ofst)


def styledstr(st: str, italic: bool=False, bold: bool=False, style: StyleType='serif'):
    ''' Apply unicode styling conversion to a string '''
    return ''.join([styledchr(s, italic, bold, style) for s in st])
