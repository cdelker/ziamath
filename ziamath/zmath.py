''' Main math rendering class '''

from __future__ import annotations
from typing import Union, Literal, Tuple, Optional, Dict
import re
from math import inf, cos, sin, radians
from itertools import zip_longest
import importlib.resources as pkg_resources
import xml.etree.ElementTree as ET

import ziafont as zf
from ziafont.glyph import fmt

from .mathfont import MathFont
from .nodes import makenode, getstyle
from .escapes import unescape
from .config import config

from latex2mathml.converter import convert  # type: ignore
import latex2mathml.commands  # type: ignore


Halign = Literal['left', 'center', 'right']
Valign = Literal['top', 'center', 'base', 'axis', 'bottom']


def denamespace(element: ET.Element) -> ET.Element:
    ''' Recursively remove namespace {...} from beginning of xml
        element names, so they can be searched easily.
    '''
    if element.tag.startswith('{'):
        element.tag = element.tag.split('}')[1]
    for elm in element:
        denamespace(elm)
    return element


def declareoperator(name: str) -> None:
    ''' Declare a new operator name, similar to Latex \DeclareMathOperator command.
        Should start with \.

        Example: declareoperator(r'\myfunc')
    '''
    latex2mathml.commands.FUNCTIONS = latex2mathml.commands.FUNCTIONS + (name,)


declareoperator(r'\tg')
declareoperator(r'\ctg')
declareoperator(r'\arcctg')
declareoperator(r'\arctg')


def tex2mml(tex: str, inline: bool = False, bigprime: bool = False) -> str:
    ''' Convert Latex to MathML. Do some hacky preprocessing to work around
        some issues with generated MathML that ziamath doesn't support yet.
    '''
    tex = re.sub(r'\\binom{(.+?)}{(.+?)}', r'\\left( \1 \\atop \2 \\right)', tex)
    tex = re.sub(r'\\mathrm{(.+?)}', r'\\mathrm {\1}', tex)  # latex2mathml bug requires space after mathrm
    
    
    if not bigprime:
        # font's prime glyph is already superscripted
        tex = re.sub(r"'", r'\\prime', tex)
        tex = re.sub(r'\^\\prime', r'\\prime', tex)
        tex = re.sub(r'\^\\dprime', r'\\dprime', tex)
        tex = re.sub(r'\^″', r'″', tex)  # double prime
        tex = re.sub(r'\^\\trprime', r'\\trprime', tex)
        tex = re.sub(r'\^‴', r'‴', tex)  # triple prime
        tex = re.sub(r'\^\\qprime', r'\\qprime', tex)
        tex = re.sub(r'\^⁗', r'⁗', tex)  # quadruple prime
        tex = re.sub(r'\^\\backprime', r'\\backprime', tex)
        tex = re.sub(r'\^‵', r'‵', tex)  # back prime
        tex = re.sub(r'\^\\backdprime', r'\\backdprime', tex)
        tex = re.sub(r'\^‶', r'‶', tex)  # back prime
        tex = re.sub(r'\^\\backtrprime', r'\\backtrprime', tex)
        tex = re.sub(r'\^‷', r'‷', tex)  # back prime

    mml = convert(tex, display='inline' if inline else 'block')

    # Replace some operators with "stretchy" variants
    mml = re.sub(r'<mo>&#x0005E;', r'<mo>&#x00302;', mml)  # widehat
    mml = re.sub(r'<mo>&#x0007E;', r'<mo>&#x00303;', mml)  # widetilde
    return mml
    

def font_has_bigprime(font: str = None) -> bool:
    ''' Determine whether font uses a large prime glyph, or
        a prime glyph already in the superscript position
    '''
    if font is None:
        loadedfont = loadedfonts.get('default')
    elif font in loadedfonts:
        loadedfont = loadedfonts.get(font)
    else:
        loadedfont = MathFont(font)
        loadedfonts[font] = loadedfont
    return loadedfont.math.bigprime  # type:ignore


class Math:
    ''' MathML Element Renderer

        Args:
            mathml: MathML expression, in string or XML Element
            size: Base font size, pixels
            font: Filename of font file. Must contain MATH typesetting table.
    '''
    # Math class doesn't have a color parameter since color is set
    # by the <mathcolor> tags in MML. Since Math is a single line,
    # alignment is done at the drawon function rather than the class level.
    def __init__(self, mathml: Union[str, ET.Element],
                 size: float=24, font: str=None):
        self.mathml = mathml
        self.size = size

        if font is None:
            self.font = loadedfonts.get('default')
        elif font in loadedfonts:
            self.font = loadedfonts.get(font)
        else:
            self.font = MathFont(font, size)
            loadedfonts[font] = self.font

        if isinstance(mathml, str):
            mathml = unescape(mathml)
            mathml = ET.fromstring(mathml)
        mathml = denamespace(mathml)

        self.style = getstyle(mathml)
        self.element = mathml
        self.node = makenode(mathml, parent=self)  # type: ignore

    @classmethod
    def fromlatex(cls, latex: str, size: float=24, mathstyle: str=None,
                  font: str=None, color: str=None, inline: bool = False):
        ''' Create Math Renderer from a single LaTeX expression. Requires
            latex2mathml Python package.

            Args:
                latex: Latex string
                size: Base font size
                mathstyle: Style parameter for math, equivalent to "mathvariant" MathML attribute
                font: Font file name
                color: Color parameter, equivalent to "mathcolor" attribute
                inline: Use inline math mode (default is block mode)
        '''
        mathml: Union[str, ET.Element]
        mathml = tex2mml(latex, inline=inline, bigprime=font_has_bigprime(font))
        if mathstyle:
            mathml = ET.fromstring(mathml)
            mathml.attrib['mathvariant'] = mathstyle
            mathml = ET.tostring(mathml, encoding='unicode')
        if color:
            mathml = ET.fromstring(mathml)
            mathml.attrib['mathcolor'] = color
        return cls(mathml, size, font)

    @classmethod
    def fromlatextext(cls, latex: str, size: float=24, mathstyle: str=None,
                      textstyle: str=None, font: str=None,
                      color: str=None):
        ''' Create Math Renderer from a sentence containing zero or more LaTeX
            expressions delimited by $..$, resulting in single MathML element.
            Requires latex2mathml Python package.

            Args:
                latex: string
                size: Base font size
                mathstyle: Style parameter for math, equivalent to "mathvariant" MathML attribute
                textstyle: Style parameter for text, equivalent to "mathvariant" MathML attribute
                font: Font file name
                color: Color parameter, equivalent to "mathcolor" attribute
        '''
        # Extract each $..$, convert to MathML, but the raw text in <mtext>, and join
        # into a single <math>
        parts = re.split(r'\$(.*?)\$', latex)
        texts = parts[::2]
        bigprime = font_has_bigprime(font)
        maths = [tex2mml(p, inline=True, bigprime=bigprime) for p in parts[1::2]]
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
        if color:
            mml.attrib['mathcolor'] = color
        return cls(mml, size, font)

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
        if not config.svg2:
            svg.attrib['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
        svg.attrib['viewBox'] = f'{fmt(bbox.xmin-1)} {fmt(-bbox.ymax-1)} {fmt(width)} {fmt(height)}'
        return svg

    def drawon(self, svg: ET.Element, x: float=0, y: float=0,
               halign: Halign='left', valign: Valign='base') -> ET.Element:
        ''' Draw the math expression on an existing SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: The image (top-level svg XML object) to draw on
                halign: Horizontal alignment
                valign: Vertical alignment

            Note: Horizontal alignment can be the typical 'left', 'center', or 'right'.
            Vertical alignment can be 'top', 'bottom', or 'center' to align with the
            expression's bounding box, or 'base' to align with the bottom
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


class Latex(Math):
    ''' Render Math from LaTeX

        Args:
            latex: Latex string
            size: Base font size
            mathstyle: Style parameter for math, equivalent to "mathvariant" MathML attribute
            font: Font file name
            color: Color parameter, equivalent to "mathcolor" attribute
            inline: Use inline math mode (default is block mode)
        '''
    def __init__(self, latex: str, size: float=24, mathstyle: str=None,
                 font: str=None, color: str=None, inline: bool = False):
        self.latex = latex
        
        mathml: Union[str, ET.Element]
        mathml = tex2mml(latex, inline=inline, bigprime=font_has_bigprime(font))
        if mathstyle:
            mathml = ET.fromstring(mathml)
            mathml.attrib['mathvariant'] = mathstyle
            mathml = ET.tostring(mathml, encoding='unicode')
        if color:
            mathml = ET.fromstring(mathml)
            mathml.attrib['mathcolor'] = color
        super().__init__(mathml, size, font)


class Text:
    ''' Mixed text and latex math. Inline math delimited by single $..$, and
        display-mode math delimited by double $$...$$. Can contain multiple
        lines. Drawn to SVG.

        Args:
            s: string to write
            textfont: font filename or family name for text
            mathfont: font filename for math
            mathstyle: Style parameter for math
            size: font size in points
            linespacing: spacing between lines
            color: color of text
            halign: horizontal alignment
            valign: vertical alignment
            rotation: Rotation angle in degrees
            rotation_mode: Either 'default' or 'anchor', to
                mimic Matplotlib behavoir. See:
                https://matplotlib.org/stable/gallery/text_labels_and_annotations/demo_text_rotation_mode.html

    '''
    def __init__(self, s, textfont: str=None, mathfont: str=None,
                 mathstyle: str=None, size: float=24, linespacing: float=1,
                 color: str=None,
                 halign: str='left', valign: str='base',
                 rotation: float=0, rotation_mode: str='anchor'):
        self.str = s
        self.mathfont = mathfont
        self.mathstyle = mathstyle
        self.size = size
        self.linespacing = linespacing
        self.color = color
        self._halign = halign
        self._valign = valign
        self.rotation = rotation
        self.rotation_mode = rotation_mode
        self.textfont: Optional[Union[MathFont, zf.Font]]

        # textfont can be a path to font, or style type like "serif".
        # If style type, use Stix font variation
        if textfont is None:
            textfont = 'sans'
        if textfont in ['sans', 'sans-serif', 'serif']:
            self.textfont = None
            self.textstyle = textfont
        else:
            self.textfont = zf.Font(textfont)
            self.textstyle = 'sans'

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
        if not config.svg2:
            svg.attrib['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
        svg.attrib['viewBox'] = f'{fmt(x1)} {fmt(y1)} {fmt(x2-x1)} {fmt(y2-y1)}'
        return svg

    def save(self, fname):
        ''' Save expression to SVG file '''
        with open(fname, 'w') as f:
            f.write(self.svg())

    def drawon(self, svg: ET.Element, x: float=0, y: float=0,
               halign: str=None, valign: str=None) -> ET.Element:
        ''' Draw text on existing SVG element

            Args:
                svg: Element to draw on
                x: x-position
                y: y-position
                halign: Horizontal alignment
                valign: Vertical alignment
        '''
        svgelm, _ = self._drawon(svg, x, y, halign, valign)
        return svgelm

    def _drawon(self, svg: ET.Element, x: float=0, y: float=0,
                halign: str=None, valign: str=None) -> Tuple[ET.Element, Tuple[float, float, float, float]]:
        ''' Draw text on existing SVG element

            Args:
                svg: Element to draw on
                x: x-position
                y: y-position
                halign: Horizontal alignment
                valign: Vertical alignment
        '''
        halign = self._halign if halign is None else halign
        valign = self._valign if valign is None else valign

        lines = self.str.splitlines()
        svglines = []
        svgelm = ET.SubElement(svg, 'g')

        # Split into lines and "parts"
        linesizes = []
        for line in lines:
            svgparts = []
            parts = re.split(r'(\$+.*?\$+)', line)
            partsizes = []
            for part in parts:
                if not part:
                    continue
                if part.startswith('$$') and part.endswith('$$'):  # Display-mode math
                    math = Math.fromlatex(part.replace('$', ''),
                                          font=self.mathfont,
                                          mathstyle=self.mathstyle,
                                          inline=False,
                                          size=self.size, color=self.color)
                    svgparts.append(math)
                    partsizes.append(math.getsize())
                    
                elif part.startswith('$') and part.endswith('$'):  # Text-mode Math
                    math = Math.fromlatex(part.replace('$', ''),
                                          font=self.mathfont,
                                          mathstyle=self.mathstyle,
                                          inline=True,
                                          size=self.size, color=self.color)
                    svgparts.append(math)
                    partsizes.append(math.getsize())
                else:  # Text
                    if self.textfont:
                        txt = zf.Text(part, font=self.textfont, size=self.size, color=self.color)
                        partsizes.append(txt.getsize())
                    else:
                        txt = Math.fromlatextext(part, textstyle=self.textstyle,
                                                 size=self.size, color=self.color)
                        partsizes.append((txt.node.bbox.xmax - txt.node.bbox.xmin,  # type: ignore
                                          txt.node.size))  # type: ignore
                    svgparts.append(txt)
            if len(svgparts) > 0:
                svglines.append(svgparts)
                linesizes.append(partsizes)

        lineofsts = [min([p.getyofst() for p in line]) for line in svglines]
        lineheights = [max(p[1] for p in line) for line in linesizes]
        linewidths = [sum(p[0] for p in line) for line in linesizes]

        if valign == 'bottom':
            ystart = y + sum(lineofsts) - sum(lineheights[1:])
        elif valign == 'top':
            ystart = y + lineheights[0] + lineofsts[0]
        elif valign == 'center':
            ystart = y + lineheights[0] + lineofsts[0] - sum(lineheights)/2
        else:  # 'base'
            ystart = y

        xmin = ymin = inf
        xmax = ymax = -inf
        yloc = ystart
        for i, line in enumerate(svglines):
            xloc = x
            xloc += {'left': 0,
                     'right': -linewidths[i],
                     'center': -linewidths[i]/2}.get(halign, 0)

            xmin = min(xmin, xloc)
            xmax = max(xmax, xloc+linewidths[i])

            # Include extra height of tall math expressions
            drop = 0
            if i > 0:
                try:
                    drop = min(p.node.bbox.ymin for p in line if isinstance(p, Math))
                except ValueError:
                    drop = 0

            yloc -= drop
            ymin = min(ymin, yloc-lineheights[i])
            ymax = max(ymax, yloc-lineofsts[i])
            for part, size in zip(line, linesizes[i]):
                part.drawon(svgelm, xloc, yloc)
                xloc += size[0]
            yloc += lineheights[i] * self.linespacing

        if self.rotation:
            costh = cos(radians(self.rotation))
            sinth = sin(radians(self.rotation))
            p1 = (xmin-x, ymin-y)  # Corners relative to rotation point
            p2 = (xmax-x, ymin-y)
            p3 = (xmax-x, ymax-y)
            p4 = (xmin-x, ymax-y)
            x1 = x + (p1[0]*costh + p1[1]*sinth)
            x2 = x + (p2[0]*costh + p2[1]*sinth)
            x3 = x + (p3[0]*costh + p3[1]*sinth)
            x4 = x + (p4[0]*costh + p4[1]*sinth)
            y1 = y - (p1[0]*sinth - p1[1]*costh)
            y2 = y - (p2[0]*sinth - p2[1]*costh)
            y3 = y - (p3[0]*sinth - p3[1]*costh)
            y4 = y - (p4[0]*sinth - p4[1]*costh)
            bbox = (min(x1, x2, x3, x4), max(x1, x2, x3, x4),
                    min(y1, y2, y3, y4), max(y1, y2, y3, y4))

            xform = ''
            if self.rotation_mode == 'default':
                dx = {'left': x - bbox[0],
                      'right': x - bbox[1],
                      'center': x - (bbox[1]+bbox[0])/2}.get(halign, 0)
                dy = {'top': y - bbox[2],
                      'bottom': y - bbox[3],
                      'base': -sinth*dx,
                      'center': y - (bbox[3]+bbox[2])/2}.get(valign, 0)
                xform = f'translate({dx} {dy})'
                bbox = (bbox[0]+dx, bbox[1]+dx,
                        bbox[2]+dy, bbox[3]+dy)

            xform += f' rotate({-self.rotation} {x} {y})'
            if config.debug:
                rect = ET.SubElement(svg, 'rect')
                rect.attrib['x'] = fmt(bbox[0])
                rect.attrib['y'] = fmt(bbox[2])
                rect.attrib['width'] = fmt(bbox[1]-bbox[0])
                rect.attrib['height'] = fmt(bbox[3]-bbox[2])
                rect.attrib['fill'] = 'none'
                rect.attrib['stroke'] = 'red'

            svgelm.set('transform', xform)
            xmin, xmax, ymin, ymax = bbox

        return svgelm, (xmin, xmax, ymin, ymax)

    def getsize(self):
        ''' Get pixel width and height of Text. '''
        svg = ET.Element('svg')
        _, (xmin, xmax, ymin, ymax) = self._drawon(svg)
        return (xmax-xmin, ymax-ymin)

    def bbox(self):
        ''' Get bounding box (xmin, xmax, ymin, ymax) of Text. '''
        svg = ET.Element('svg')
        _, (xmin, xmax, ymin, ymax) = self._drawon(svg)
        return (xmin, xmax, ymin, ymax)


# Cache the loaded fonts to prevent reloading all the time
with pkg_resources.path('ziamath.fonts', 'STIXTwoMath-Regular.ttf') as p:
    fontname = p
loadedfonts: Dict[str, Union[zf.Font, MathFont]] = {'default': MathFont(fontname)}
