''' <msub>, <msup>, <msubsup> Superscript and Subscript Elements '''
from __future__ import annotations
import xml.etree.ElementTree as ET

from ziafont.fonttypes import BBox

from ..mathfont import MathFont
from .. import operators
from .mnode import Mnode
from .spacing import space_ems


def place_super(base: Mnode, superscript: Mnode, font: MathFont) -> tuple[float, float, float]:
    ''' Superscript. Can be above the operator (like sum) or regular super '''
    if base.params.get('movablelimits') == 'true' and base.style.displaystyle:
        x = (-(base.bbox.xmax - base.bbox.xmin) / 2
             - (superscript.bbox.xmax - superscript.bbox.xmin) / 2)
        supy = (-base.bbox.ymax
                - base.units_to_points(font.math.consts.upperLimitGapMin)
                + superscript.bbox.ymin)
        xadvance = 0.
    else:
        x = 0.
        shiftup = font.math.consts.superscriptShiftUp

        if base.params.get('movablelimits') == 'true':
            x -= base.ems_to_pts(space_ems(base.params.get('rspace', '0')))

        if (lastg := base.lastglyph()):
            if ((italicx := font.math.italicsCorrection.getvalue(lastg.index))
                    and base.lastchar() not in operators.integrals):
                x += base.units_to_points(italicx)

            if (firstg := superscript.firstglyph()):
                if lastg.index >= 0 and font.math.kernInfo:  # assembled glyphs have idx<0
                    kern, shiftup = font.math.kernsuper(lastg, firstg)
                    x += base.units_to_points(kern)
                elif base.mtag != 'mi':
                    shiftup = (lastg.bbox.ymax
                               - base.points_to_units((superscript.bbox.ymax
                                                       - superscript.bbox.ymin)/2))

            else:  # eg ^/frac
                shiftup = lastg.bbox.ymax
                x += base.ems_to_pts(space_ems('verythinmathspace'))
        supy = base.units_to_points(-shiftup)
        xadvance = x + superscript.bbox.xmax
    return x, supy, xadvance


def place_sub(base: Mnode, subscript: Mnode, font: MathFont) -> tuple[float, float, float]:
    ''' Calculate subscript. Can be below the operator (like sum) or regular sub '''
    if base.params.get('movablelimits') == 'true' and base.style.displaystyle:
        x = -(base.bbox.xmax - base.bbox.xmin) / 2 - (subscript.bbox.xmax - subscript.bbox.xmin) / 2
        suby = (-base.bbox.ymin
                + base.units_to_points(font.math.consts.lowerLimitGapMin)
                + subscript.bbox.ymax)
        xadvance = 0.
    else:
        shiftdn = font.math.consts.subscriptShiftDown
        x = 0.

        if base.params.get('movablelimits') == 'true':
            x -= base.ems_to_pts(space_ems(base.params.get('rspace', '0')))

        if (lastg := base.lastglyph()):
            if ((italicx := font.math.italicsCorrection.getvalue(lastg.index))
                    and base.lastchar() in operators.integrals):
                x -= base.units_to_points(italicx)  # Shift back on integrals

            if (firstg := subscript.firstglyph()):
                if lastg.index > 0 and font.math.kernInfo:
                    kern, shiftdn = font.math.kernsub(lastg, firstg)
                    x += base.units_to_points(kern)
                elif base.mtag != 'mi':
                    shiftdn = (-lastg.bbox.ymin
                               + base.points_to_units((subscript.bbox.ymax
                                                       - subscript.bbox.ymin)/2))
            else:
                shiftdn = -lastg.bbox.ymin
        suby = base.units_to_points(shiftdn)
        xadvance = x + subscript.xadvance()
    return x, suby, xadvance


class Msup(Mnode, tag='msup'):
    ''' Superscript Node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        assert len(self.element) == 2
        self.base = Mnode.fromelement(self.element[0], parent=self, **kwargs)
        kwargs['sup'] = True
        self.increase_child_scriptlevel(self.element[1])
        self.superscript = Mnode.fromelement(self.element[1], parent=self, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        self.nodes.append(self.base)
        self.nodexy.append((0, 0))
        x = self.base.xadvance()

        supx, supy, xadv = place_super(self.base, self.superscript, self.font)
        self.nodes.append(self.superscript)
        self.nodexy.append((x+supx, supy))
        if self.base.bbox.ymax > self.base.bbox.ymin:
            xmin = min(self.base.bbox.xmin, x+supx+self.superscript.bbox.xmin)
            xmax = max(x + xadv, self.base.bbox.xmax, x+supx+self.superscript.bbox.xmax)
            ymin = min(self.base.bbox.ymin, -supy + self.superscript.bbox.ymin)
            ymax = max(self.base.bbox.ymax, -supy + self.superscript.bbox.ymax)
        else:  # Empty base
            xmin = self.superscript.bbox.xmin
            ymin = -supy
            xmax = x + xadv
            ymax = -supy + self.superscript.bbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Msub(Mnode, tag='msub'):
    ''' Subscript Node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        assert len(self.element) == 2
        self.base = Mnode.fromelement(self.element[0], parent=self, **kwargs)
        kwargs['sub'] = True
        self.increase_child_scriptlevel(self.element[1])
        self.subscript = Mnode.fromelement(self.element[1], parent=self, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        self.nodes.append(self.base)
        self.nodexy.append((0, 0))
        x = self.base.xadvance()

        subx, suby, xadv = place_sub(self.base, self.subscript, self.font)
        self.nodes.append(self.subscript)
        self.nodexy.append((x + subx, suby))

        xmin = min(self.base.bbox.xmin, x+subx+self.subscript.bbox.xmin)
        xmax = max(x + xadv, self.base.bbox.xmax, x+subx+self.subscript.bbox.xmax)
        ymin = min(self.base.bbox.ymin, -suby+self.subscript.bbox.ymin)
        ymax = max(self.base.bbox.ymax, -suby+self.subscript.bbox.ymax)
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Msubsup(Mnode, tag='msubsup'):
    ''' Subscript and Superscript together '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        assert len(self.element) == 3
        self.base = Mnode.fromelement(self.element[0], parent=self, **kwargs)
        kwargs['sup'] = True
        kwargs['sub'] = True
        self.increase_child_scriptlevel(self.element[1])
        self.increase_child_scriptlevel(self.element[2])
        self.subscript = Mnode.fromelement(
            self.element[1], parent=self, **kwargs)
        self.superscript = Mnode.fromelement(
            self.element[2], parent=self, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        self.nodes.append(self.base)
        self.nodexy.append((0, 0))
        x = self.base.xadvance()
        subx, suby, xadvsub = place_sub(self.base, self.subscript, self.font)
        supx, supy, xadvsup = place_super(self.base, self.superscript, self.font)

        # Ensure subSuperscriptGapMin between scripts
        if ((suby - self.subscript.bbox.ymax) - (supy-self.superscript.bbox.ymin)
                < self.units_to_points(self.font.math.consts.subSuperscriptGapMin)):
            diff = (self.units_to_points(self.font.math.consts.subSuperscriptGapMin)
                    - (suby - self.subscript.bbox.ymax)
                    + (supy-self.superscript.bbox.ymin))
            suby += diff/2
            supy -= diff/2

        self.nodes.append(self.subscript)
        self.nodexy.append((x + subx, suby))
        self.nodes.append(self.superscript)
        self.nodexy.append((x + supx, supy))

        if self.base.bbox.ymax > self.base.bbox.ymin:
            xmin = self.base.bbox.xmin
            xmax = max(x + xadvsup, x + xadvsub)
            ymin = min(-self.base.bbox.ymin, -suby + self.subscript.bbox.ymin)
            ymax = max(self.base.bbox.ymax, -supy + self.superscript.bbox.ymax)
        else:  # Empty base
            xmin = 0
            ymin = -suby
            xmax = x + max(xadvsub, xadvsup)
            ymax = -supy + self.superscript.bbox.ymax

        self.bbox = BBox(xmin, xmax, ymin, ymax)
