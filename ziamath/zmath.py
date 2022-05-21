''' Main math rendering class '''

from __future__ import annotations
from typing import Union, Literal, Tuple
import re
from math import inf
from itertools import zip_longest
import importlib.resources as pkg_resources
import xml.etree.ElementTree as ET

import ziafont as zf
from ziafont.glyph import fmt

from .mathfont import MathFont
from .nodes import makenode, getstyle
from .escapes import unescape

try:
    from latex2mathml.converter import convert  # type: ignore
except ImportError:
    convert = False


Halign = Literal['left', 'center', 'right']
Valign = Literal['top', 'center', 'baseline', 'axis', 'bottom']


def set_precision(p: int) -> None:
    ''' Set decimal precision for SVG coordinates '''
    zf.set_precision(p)


def denamespace(element: ET.Element) -> ET.Element:
    ''' Recursively remove namespace {...} from beginning of xml
        element names, so they can be searched easily.
    '''
    if element.tag.startswith('{'):
        element.tag = element.tag.split('}')[1]
    for elm in element:
        denamespace(elm)
    return element


def tex2mml(tex: str) -> str:
    ''' Convert Latex to MathML. Do some hacky preprocessing to work around
        some issues with generated MathML that ziamath doesn't support yet.
    '''
    tex = re.sub(r'\\binom{(.+?)}{(.+?)}', r'\\left( \1 \\atop \2 \\right)', tex)
    tex = re.sub(r'\\mathrm{(.+?)}', r'\\mathrm {\1}', tex)  # latex2mathml bug requires space after mathrm
    return convert(tex)


class Math:
    ''' Math Renderer

        Args:
            mathml: MathML expression, in string or XML Element
            size: Base font size, pixels
            font: Filename of font file. Must contain MATH typesetting table.
            svg2: Use SVG2.0 specification. Disable for compatibility.
    '''
    def __init__(self, mathml: Union[str, ET.Element],
                 size: float=24, font: str=None, svg2: bool=True):
        self.mathml = mathml
        self.size = size

        if font is None:
            self.font = loadedfonts.get('default')
        elif font in loadedfonts:
            self.font = loadedfonts.get(font)
        else:
            self.font = MathFont(font, size)
            loadedfonts[font] = self.font

        self.font.svg2 = svg2  # type:ignore
        if isinstance(mathml, str):
            mathml = unescape(mathml)
            mathml = ET.fromstring(mathml)
        mathml = denamespace(mathml)

        self.style = getstyle(mathml)
        self.element = mathml
        self.node = makenode(mathml, parent=self, size=size)  # type: ignore

    @classmethod
    def fromlatex(cls, latex: str, size: float=24, mathstyle: str=None, color: str=None, font: str=None, svg2: bool=True):
        ''' Create Math Renderer from a single LaTeX expression. Requires
            latex2mathml Python package.

            Args:
                latex: Latex string
                size: Base font size
                mathstyle: Style parameter for math, equivalent to "mathvariant" MathML attribute
                color: Color parameter, equivalent to "mathcolor" attribute
                font: Font file name
                svg2: Use SVG2.0 specification. Disable for compatibility.
        '''
        if not convert:
            raise ValueError('fromlatex requires latex2mathml package.')

        mathml: Union[str, ET.Element]
        mathml = tex2mml(latex)
        if mathstyle:
            mathml = ET.fromstring(mathml)
            mathml.attrib['mathvariant'] = mathstyle
            mathml = ET.tostring(mathml, encoding='unicode')
        if color:
            mathml = ET.fromstring(mathml)
            mathml.attrib['mathcolor'] = color
        return cls(mathml, size, font, svg2=svg2)

    @classmethod
    def fromlatextext(cls, latex: str, size: float=24, mathstyle: str=None,
                      textstyle: str=None, font: str=None, svg2=True):
        ''' Create Math Renderer from a sentance containing zero or more LaTeX
            expressions delimited by $..$, resulting in single MathML element.
            Requires latex2mathml Python package.

            Args:
                latex: string
                size: Base font size
                mathstyle: Style parameter for math, equivalent to "mathvariant" MathML attribute
                textstyle: Style parameter for text, equivalent to "mathvariant" MathML attribute
                font: Font file name
                svg2: Use SVG2.0 specification. Disable for compatibility.
        '''
        # Extract each $..$, convert to MathML, but the raw text in <mtext>, and join
        # into a single <math>
        parts = re.split(r'\$(.*?)\$', latex)
        texts = parts[::2]
        maths = [tex2mml(p) for p in parts[1::2]]
        mathels = [ET.fromstring(m)[0] for m in maths]   # Convert to xml, but drop opening <math>
        mml = ET.Element('math')
        for text, mathel in zip_longest(texts, mathels):
            if text:
                mtext = ET.SubElement(mml, 'mtext')
                if textstyle:
                    mtext.attrib['mathvariant'] = textstyle
                mtext.text = text
            if mathel is not None:
                if mathstyle:
                    mathel.attrib['mathvariant'] = mathstyle
                mml.append(mathel)
        return cls(mml, size, font, svg2=svg2)

    def svgxml(self) -> ET.Element:
        ''' Get standalone SVG of expression as XML Element Tree '''
        svg = ET.Element('svg')
        self.node.draw(1, 0, svg)
        bbox = self.node.bbox
        width = bbox.xmax - bbox.xmin + 2  # Add a 1-px border
        height = bbox.ymax - bbox.ymin + 2

        # Note: viewbox goes negative.
        svg.attrib['width'] = fmt(width)
        svg.attrib['height'] = fmt(height)
        svg.attrib['xmlns'] = 'http://www.w3.org/2000/svg'
        if not self.font.svg2:  # type: ignore
            svg.attrib['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
        svg.attrib['viewBox'] = f'{fmt(bbox.xmin-1)} {fmt(-bbox.ymax-1)} {fmt(width)} {fmt(height)}'
        return svg

    def drawon(self, svg: ET.Element, x: float=0, y: float=0,
               color: str=None,
               halign: Halign='left', valign: Valign='baseline') -> ET.Element:
        ''' Draw the math expression on an existing SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: The image (top-level svg XML object) to draw on
                color: Color name or #000000 hex code
                halign: Horizontal alignment
                valign: Vertical alignment

            Note: Horizontal alignment can be the typical 'left', 'center', or 'right'.
            Vertical alignment can be 'top', 'bottom', or 'center' to align with the
            expression's bounding box, or 'baseline' to align with the bottom
            of the first text element, or 'axis', aligning with the height of a minus
            sign above the baseline.
        '''
        width, height = self.getsize()
        yshift = {'top': self.node.bbox.ymax,
                  'center': height/2 + self.node.bbox.ymin,
                  'axis': self.font.math.consts.axisHeight * self.node.emscale,  # type: ignore
                  'bottom': self.node.bbox.ymin}.get(valign, 0)
        xshift = {'center': -width/2,
                  'right': -width}.get(halign, 0)

        svgelm = ET.SubElement(svg, 'g')  # Put it in a group
        if color:
            svgelm.attrib['fill'] = color
        self.node.draw(x+xshift, y+yshift, svgelm)
        return svgelm

    def svg(self) -> str:
        ''' Get expression as SVG string '''
        return ET.tostring(self.svgxml(), encoding='unicode')

    def save(self, fname):
        ''' Save expression to SVG file '''
        with open(fname, 'w') as f:
            f.write(self.svg())

    def _repr_svg_(self):
        ''' Jupyter SVG representation '''
        return self.svg()

    @classmethod
    def mathml2svg(cls, mathml: Union[str, ET.Element],
                   size: float=24, font: str=None):
        ''' Shortcut to just return SVG string directly '''
        return cls(mathml, size=size, font=font).svg()

    def getsize(self) -> tuple[float, float]:
        ''' Get size of rendered text '''
        return (self.node.bbox.xmax - self.node.bbox.xmin,
                self.node.bbox.ymax - self.node.bbox.ymin)
    
    def getyofst(self) -> float:
        ''' Y-shift from bottom of bbox to 0 '''
        return self.node.bbox.ymin


class Text:
    ''' Mixed text and latex math, with math delimited by $..$. Drawn to SVG.

        Args:
            s: string to write
            textfont: font filename or family name for text
            mathfont: font filename or family name for math
            mathstyle: Style parameter for math
            size: font size in points
            linespacing: spacing between lines
            halign: horizontal alignment
            valign: vertical alignment
            svg2: Use SVG version 2.0. Disable for better
                browser compatibility.
    '''
    def __init__(self, s, textfont: str=None, mathfont: str=None,
                 mathstyle: str=None, size: float=24, linespacing: float=1,
                 halign: str='left', valign: str='base',
                 svg2=True):
        self.str = s
        self.textfont = zf.Font(textfont, svg2=svg2)
        self.mathfont = mathfont
        self.mathstyle = mathstyle
        self.size = size
        self.linespacing = linespacing
        self._svg2 = svg2
        self._halign = halign
        self._valign = valign

    def svg(self) -> str:
        ''' Get expression as SVG string '''
        return ET.tostring(self.svgxml(), encoding='unicode')

    def _repr_svg_(self):
        ''' Jupyter SVG representation '''
        return self.svg()

    def svgxml(self) -> ET.Element:
        ''' Get standalone SVG of expression as XML Element Tree '''
        svg = ET.Element('svg')
        svgelm, (x1, x2, y1, y2) = self._drawon(svg)
        svg.attrib['width'] = fmt(x2-x1)
        svg.attrib['height'] = fmt(y2-y1)
        svg.attrib['xmlns'] = 'http://www.w3.org/2000/svg'
        if not self._svg2:  # type: ignore
            svg.attrib['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
        svg.attrib['viewBox'] = f'{fmt(x1)} {fmt(y1)} {fmt(x2-x1)} {fmt(y2-y1)}'
        return svg

    def save(self, fname):
        ''' Save expression to SVG file '''
        with open(fname, 'w') as f:
            f.write(self.svg())

    def drawon(self, svg: ET.Element, x: float=0, y: float=0, color: str='black',
               halign: str='left', valign: str='bottom') -> ET.Element:
        ''' Draw text on existing SVG element

            Args:
                svg: Element to draw on
                x: x-position
                y: y-position
                color: color of text
                halign: Horizontal alignment
                valign: Vertical alignment
        '''
        svgelm, _ = self._drawon(svg, x, y, color, halign, valign)
        return svgelm
        
    def _drawon(self, svg: ET.Element, x: float=0, y: float=0,
                color: str='black', halign: str=None,
                valign: str=None) -> Tuple[ET.Element, Tuple[float, float, float, float]]:
        ''' Draw text on existing SVG element

            Args:
                svg: Element to draw on
                x: x-position
                y: y-position
                color: color of text
                halign: Horizontal alignment
                valign: Vertical alignment
        '''
        halign = self._halign if halign is None else halign
        valign = self._valign if valign is None else valign
        
        lines = self.str.splitlines()
        svglines = []
        svgelm = ET.SubElement(svg, 'g')

        # Split into lines and "parts"
        for line in lines:
            svgparts = []
            parts = re.split(r'(\$.*?\$)', line)
            for part in parts:
                if not part:
                    continue
                if part.startswith('$') and part.endswith('$'):  # Math
                    math = Math.fromlatex(part.replace('$', ''), font=self.mathfont,
                                          mathstyle=self.mathstyle,
                                          size=self.size, svg2=self._svg2)
                    svgparts.append(math)
                else:  # Text
                    txt = zf.Text(part, font=self.textfont, size=self.size, svg2=self._svg2)
                    svgparts.append(txt)
            if len(svgparts):
                svglines.append(svgparts)

        linesizes = [[p.getsize() for p in line] for line in svglines]
        lineheights = [max(p[1] for p in line) for line in linesizes]
        linewidths = [sum(p[0] for p in line) for line in linesizes]
        lineofsts = [min(p.getyofst() for p in line) for line in svglines]

        if valign == 'bottom':
            yloc = y + sum(lineofsts) - sum(lineheights[1:])
        elif valign == 'top':
            yloc = y + lineheights[0] + lineofsts[0]
        elif valign == 'center':
            yloc = y + lineheights[0] + lineofsts[0] - sum(lineheights)/2
        else:  # 'base'
            yloc = y
            
        xmin = ymin = inf
        xmax = ymax = -inf
        for i, line in enumerate(svglines):
            xloc = x
            sizes = [p.getsize() for p in line]

            xloc += {'left': 0,
                     'right': -linewidths[i],
                     'center': -linewidths[i]/2}.get(halign, 0)

            xmin = min(xmin, xloc)
            xmax = max(xmax, xloc+linewidths[i])
            ymin = min(ymin, yloc-lineheights[i])
            ymax = max(ymax, yloc+lineheights[i])
            
            try:
                drop = min(p.node.bbox.ymin for p in line if isinstance(p, Math))
            except ValueError:
                drop = 0
            if i > 0 and lineheights[i] > self.linespacing * self.size:
                yloc += (lineheights[i] - self.linespacing * self.size)
            for part, size in zip(line, sizes):
                part.drawon(svgelm, xloc, yloc)
                xloc += size[0]
            yloc += self.linespacing * self.size
            yloc -= drop

        if color:
            svgelm.attrib['fill'] = color

        return svgelm, (xmin, xmax, ymin, ymax)


# Cache the loaded fonts to prevent reloading all the time
with pkg_resources.path('ziamath.fonts', 'STIXTwoMath-Regular.ttf') as p:
    fontname = p
loadedfonts = {'default': MathFont(fontname)}
