''' Main math rendering class '''

from typing import Union
import importlib.resources as pkg_resources
import xml.etree.ElementTree as ET

import ziafont as zf

from .mathfont import MathFont
from .nodes import makenode, getstyle
from .mathtable import MathTable
from .escapes import unescape

try:
    from latex2mathml.converter import convert  # type: ignore
except ImportError:
    convert = False


def denamespace(element: ET.Element) -> ET.Element:
    ''' Recursively remove namespace {...} from beginning of xml
        element names, so they can be searched easily.
    '''
    if element.tag.startswith('{'):
        element.tag = element.tag.split('}')[1]
    for elm in element:
        denamespace(elm)
    return element


class Math:
    ''' Math Renderer

        Args:
            mathml: MathML expression, in string or XML Element
            size: Base font size, pixels
            font: Filename of font file. Must contain MATH typesetting table.
    '''
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
        self.node = makenode(mathml, parent=self, size=size)  # type: ignore

    @classmethod
    def fromlatex(cls, latex: str, size: float=24, font: str=None):
        ''' Create Math Renderer from LaTeX expression. Requires
            latex2mathml Python package.

            Args:
                latex: Latex string
                size: Base font size
                font: Font file name
        '''
        if not convert:
            raise ValueError('fromlatex requires latex2mathml package.')
        mathml = convert(latex)
        return cls(mathml, size, font)

    def svgxml(self) -> ET.Element:
        ''' Get standalone SVG of expression as XML Element Tree '''
        svg = ET.Element('svg')
        self.node.draw(1, 0, svg)
        bbox = self.node.bbox
        width = bbox.xmax - bbox.xmin + 2  # Add a 1-px border
        height = bbox.ymax - bbox.ymin + 2

        # Note: viewbox goes negative.
        svg.attrib['width'] = str(width)
        svg.attrib['height'] = str(height)
        svg.attrib['xmlns'] = 'http://www.w3.org/2000/svg'
        svg.attrib['viewBox'] = f'0 {-bbox.ymax-1} {width} {height}'
        return svg

    def drawon(self, x: float, y: float, svg: ET.Element) -> None:
        ''' Draw the math expression on an existing SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: The image (XML object) to draw on
        '''
        self.node.draw(x, y, svg)

    def svg(self) -> str:
        ''' Get expression as SVG string '''
        return ET.tostring(self.svgxml(), encoding='unicode')

    def _repr_svg_(self):
        ''' Jupyter SVG representation '''
        return self.svg()

    @classmethod
    def mathml2svg(cls, mathml: Union[str, ET.Element],
                   size: float=24, font: str=None):
        ''' Shortcut to just return SVG string directly '''
        return cls(mathml, size=size, font=font).svg()


# Cache the loaded fonts to prevent reloading all the time
with pkg_resources.path('ziamath.fonts', 'STIXTwoMath-Regular.ttf') as p:
    fontname = p
loadedfonts = {'default': MathFont(fontname)}
