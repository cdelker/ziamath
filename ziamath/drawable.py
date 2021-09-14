from __future__ import annotations
from typing import Optional, Union, MutableMapping

import math
import xml.etree.ElementTree as ET

from ziafont import Font
from ziafont.fonttypes import BBox
from ziafont.glyph import SimpleGlyph


class Drawable:
    ''' Base class for drawable nodes '''

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        return None
        
    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        return None

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        raise NotImplementedError

        
class Glyph(Drawable):
    ''' A single glyph '''
    def __init__(self, glyph: SimpleGlyph, char: str, size: float, emscale: float,
                 style: MutableMapping[str, Union[str, bool]]=None, **kwargs):
        self.glyph = glyph
        self.char = char
        self.size = size
        self.emscale = emscale
        self.phantom = kwargs.get('phantom', False)
        self.style = style if style is not None else {}
        self._setup()

    def _setup(self, **kwargs) -> None:
        ''' Place the glyphs with 0, 0 positions '''
        self.bbox = BBox(
            self.glyph.path.bbox.xmin * self.emscale,
            self.glyph.path.bbox.xmax * self.emscale,
            self.glyph.path.bbox.ymin * self.emscale,
            self.glyph.path.bbox.ymax * self.emscale)

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        return self.glyph

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        return self.glyph

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        return self.char

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        symbols = svg.findall('symbol')
        symids = [sym.attrib.get('id') for sym in symbols]
        if self.glyph.id not in symids and self.glyph.font.svg2:
            svg.append(self.glyph.svgsymbol())
        if not self.phantom:
            svg.append(self.glyph.place(x, y, self.size))
            if 'mathcolor' in self.style:
                svg[-1].set('fill', self.style['mathcolor'])  # type: ignore
        x += self.glyph.advance() * self.emscale
        return x, y


class HLine(Drawable):
    ''' Horizontal Line. '''
    def __init__(self, length: float, lw: float, style: MutableMapping[str, Union[str, bool]]=None, **kwargs):
        self.length = length
        self.lw = lw
        self.phantom = kwargs.get('phantom', False)
        self.bbox = BBox(0, lw/2, self.length, self.lw)
        self.style = style if style is not None else {}

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        if not self.phantom:
            # Use rectangle so it can change color with 'fill' attribute
            # and not mess up glyphs with 'stroke' attribute
            bar = ET.SubElement(svg, 'rect')
            bar.attrib['x'] = str(x)
            bar.attrib['y'] = str(y)
            bar.attrib['width'] = str(self.length)
            bar.attrib['height'] = str(self.lw)
            if 'mathcolor' in self.style:
                bar.attrib['fill'] = self.style['mathcolor']  # type: ignore
        return x+self.length, y

    
class VLine(Drawable):
    ''' Vertical Line. '''
    def __init__(self, height: float, lw: float, style: MutableMapping[str, Union[str, bool]]=None, **kwargs):
        self.height = height
        self.lw = lw
        self.phantom = kwargs.get('phantom', False)
        self.bbox = BBox(0, self.lw, 0, self.height)
        self.style = style if style is not None else {}

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        if not self.phantom:
            # Use rectangle so it can change color with 'fill' attribute
            # and not mess up glyphs with 'stroke' attribute
            bar = ET.SubElement(svg, 'rect')
            bar.attrib['x'] = str(x-self.lw/2)
            bar.attrib['y'] = str(y)
            bar.attrib['width'] = str(self.lw)
            bar.attrib['height'] = str(self.height)
            if 'mathcolor' in self.style:
                bar.attrib['fill'] = self.style['mathcolor']  # type: ignore
        return x, y
    
    
class Box(Drawable):
    ''' Box '''
    def __init__(self, width: float, height: float, lw: float,
                 cornerradius: float=None,
                 style: MutableMapping[str, Union[str, bool]]=None, **kwargs):
        self.width = width
        self.height = height
        self.cornerradius = cornerradius
        self.lw = lw
        self.phantom = kwargs.get('phantom', False)
        self.bbox = BBox(0, self.width, 0, self.height)
        self.style = style if style is not None else {}

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        if not self.phantom:
            bar = ET.SubElement(svg, 'rect')
            bar.set('x', str(x))
            bar.set('y', str(y-self.height))
            bar.set('width', str(self.width))
            bar.set('height', str(self.height))
            bar.set('stroke-width', str(self.lw))
            bar.set('stroke', self.style.get('mathcolor', 'black'))  # type: ignore
            bar.set('fill', self.style.get('mathbackground', 'none'))  # type: ignore
            if self.cornerradius:
                bar.set('rx', str(self.cornerradius))
                
        return x+self.width, y


class Diagonal(Drawable):
    ''' Diagonal Line - corners of Box '''
    def __init__(self, width: float, height: float, lw: float,
                 arrow: bool=False,
                 style: MutableMapping[str, Union[str, bool]]=None, **kwargs):
        self.width = width
        self.height = height
        self.lw = lw
        self.arrow = arrow
        self.phantom = kwargs.get('phantom', False)
        self.bbox = BBox(0, self.width, 0, self.height)
        self.style = style if style is not None else {}
        
        self.arroww = self.width
        self.arrowh = self.height
        if self.arrow:
            # Bbox needs to be a bit bigger to accomodate arrowhead
            theta = math.atan2(-self.height, self.width)
            self.arroww = (10+self.lw*2) * math.cos(theta)
            self.arrowh = (10+self.lw*2) * math.sin(theta)

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        if not self.phantom:
            bar = ET.SubElement(svg, 'path')
            if self.arrow:
                arrowdef = ET.SubElement(svg, 'defs')
                marker = ET.SubElement(arrowdef, 'marker')
                marker.set('id', 'arrowhead')
                marker.set('markerWidth', '10')
                marker.set('markerHeight', '7')
                marker.set('refX', '0')
                marker.set('refY', '3.5')
                marker.set('orient', 'auto')
                poly = ET.SubElement(marker, 'polygon')
                poly.set('points', '0 0 10 3.5 0 7')

            bar.set('d', f'M {x} {y-self.height} L {x+self.width} {y}')
            bar.set('stroke-width', str(self.lw))
            bar.set('stroke', self.style.get('mathcolor', 'black'))  # type: ignore
            if self.arrow:
                bar.set('marker-end', 'url(#arrowhead)')
                
        return x+self.width, y

    
class Ellipse(Drawable):
    ''' Ellipse '''
    def __init__(self, width: float, height: float, lw: float,
                 style: MutableMapping[str, Union[str, bool]]=None, **kwargs):
        self.width = width
        self.height = height
        self.lw = lw
        self.phantom = kwargs.get('phantom', False)
        self.bbox = BBox(0, self.width, 0, self.height)
        self.style = style if style is not None else {}

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        if not self.phantom:
            bar = ET.SubElement(svg, 'ellipse')
#  <ellipse cx="100" cy="50" rx="100" ry="50" />

            bar.set('cx', str(x+self.width/2))
            bar.set('cy', str(y-self.height/2))
            bar.set('rx', str(self.width/2))
            bar.set('ry', str(self.height/2))
            bar.set('stroke-width', str(self.lw))
            bar.set('stroke', self.style.get('mathcolor', 'black'))  # type: ignore
            bar.set('fill', self.style.get('mathbackground', 'none'))  # type: ignore
        return x+self.width, y
    
    


#class Box(Primitive):