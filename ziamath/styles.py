''' Apply italic, bold, and other font styles by shifting the unstyled ASCII
    characters [A-Z, a-z, and 0-9] to their higher unicode alternatives. Note
    this does not check whether the new character glyph exists in the font.
'''

from __future__ import annotations
from typing import Any, MutableMapping
from collections import ChainMap
from dataclasses import dataclass, asdict
from xml.etree import ElementTree as ET


VARIANTS = ['serif', 'sans', 'script', 'double', 'mono', 'fraktur']


@dataclass
class MathVariant:
    ''' Math font variant, such as serif, sans, script, italic, etc. '''
    style: str = 'serif'
    italic: bool = False
    bold: bool = False
    normal: bool = False


@dataclass
class MathStyle:
    ''' Math Style parameters '''
    mathvariant: MathVariant = MathVariant()
    displaystyle: bool = True
    mathcolor: str = 'black'
    mathbackground: str = 'none'
    mathsize: str = ''
    scriptlevel: int = 0


def parse_variant(variant: str, parent_variant: MathVariant) -> MathVariant:
    ''' Extract mathvariant from MathML attribute and parent's variant '''
    bold = True if 'bold' in variant else parent_variant.bold
    italic = True if 'italic' in variant else parent_variant.italic
    normal = True if 'normal' in variant else parent_variant.normal

    variant = variant.replace('bold', '').replace('italic', '').strip()
    if variant in VARIANTS:
        style = variant
    else:
        style = parent_variant.style

    return MathVariant(style=style, italic=italic, bold=bold, normal=normal)

    
def parse_displaystyle(params: MutableMapping[str, Any]) -> bool:
    ''' Extract displaystyle mode from MathML attributes '''
    dstyle = True
    if 'displaystyle' in params:
        dstyle = params.get('displaystyle') in ['true', True]
    elif 'display' in params:
        dstyle = params.get('display', 'block') != 'inline'
    return dstyle


def parse_style(element: ET.Element, parent_style: MathStyle = None) -> MathStyle:
    ''' Read element style attributes into MathStyle '''
    params: MutableMapping[str, Any]
    if parent_style:
        params = ChainMap(element.attrib, asdict(parent_style))
        parent_variant = parent_style.mathvariant
    else:
        params = element.attrib
        parent_variant = MathVariant()

    args: dict[str, Any] = {}
    args['mathcolor'] = params.get('mathcolor', 'black')
    args['mathbackground'] = params.get('mathbackground', 'none')
    args['mathsize'] = params.get('mathsize', '')
    args['scriptlevel'] = int(params.get('scriptlevel', 0))
    args['mathvariant'] = parse_variant(element.attrib.get('mathvariant', ''), parent_variant) 
    args['displaystyle'] = parse_displaystyle(params)
    return MathStyle(**args)


def styledchr(c: str, style: MathStyle) -> str:
    ''' Convert an ASCII character into it's styled unicode counterpart '''
    ordc = ord(c)
    if not ((0x41 <= ordc <= 0x5A) or (0x61 <= ordc <= 0x7A) or (0x30 <= ordc <= 0x39)):
        return c

    italic = style.mathvariant.italic
    bold = style.mathvariant.bold

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

    cx = replace.get((style.mathvariant.style, italic, bold), {}).get(c)
    if cx is not None:
        return cx

    # Other replacement characters can be selected by offset
    if (0x30 <= ordc <= 0x39):  # Digit
        #        style    bold
        ofst = {('serif', True): 0x1D7CE,
                ('double', False): 0x1D7D8,
                ('sans', False): 0x1D7E2,
                ('sans', True): 0x1D7EC,
                ('mono', False): 0x1D7F6}.get((style.mathvariant.style, bold))

        if ofst is None:
            return c
        return chr(ordc - ord('0') + ofst)

    if (0x61 <= ordc <= 0x7A):
        # Lowercase
        base = ordc - 6 - ord('A')
    else:
        base = ordc - ord('A')

    ofst = None
    if style.mathvariant.style == 'serif':
        ofst = {(False, True): 0x1D400,
                (True, False): 0x1D434,
                (True, True): 0x1D468}.get((italic, bold))
    elif style.mathvariant.style == 'sans':
        ofst = {(False, False): 0x1D5A0,
                (False, True): 0x1D5D4,
                (True, False): 0x1D608,
                (True, True): 0x1D63C}.get((italic, bold))
    elif style.mathvariant.style == 'script':
        ofst = {False: 0x1D49C,
                True: 0x1D4D0}.get(bold)
    elif style.mathvariant.style == 'fraktur':
        ofst = {False: 0x1D504,
                True: 0x1D504}.get(bold)
    elif style.mathvariant.style == 'mono':
        ofst = 0x1D670
    elif style.mathvariant.style == 'double':
        ofst = 0x1D538

    if ofst is None:
        return c
    return chr(base + ofst)


def styledstr(st: str, style: MathStyle) -> str:
    ''' Apply unicode styling conversion to a string '''
    return ''.join([styledchr(s, style) for s in st])
