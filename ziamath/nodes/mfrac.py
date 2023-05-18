''' <mfrac> math element '''
from xml.etree import ElementTree as ET

from ziafont.fonttypes import BBox

from ..styles import parse_style
from ..drawable import HLine
from . import Mnode
from .spacing import space_ems, topoints


class Mfrac(Mnode, tag='mfrac'):
    ''' Fraction node '''
    # TODO: bevelled attribute for x/y fractions with slanty bar
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        pre_style = parse_style(element, parent.style)

        # check original mml attribute for displaystyle to see if
        # it was explicitly turned on (eg dfrac) and not inherited
        if (element.attrib.get('displaystyle') != 'true'
            and ('sup' in kwargs
                 or 'sub' in kwargs
                 or 'frac' in kwargs
                 or not pre_style.displaystyle)):
            element.set('scriptlevel', str(pre_style.scriptlevel + 1))

        # super() after determining scriptlevel so that scale factors are calculated
        super().__init__(element, parent, **kwargs)
        assert len(self.element) == 2
        kwargs['frac'] = True
        kwargs.pop('sup', None)
        self.numerator = Mnode.fromelement(self.element[0], parent=self, **kwargs)
        self.denominator = Mnode.fromelement(self.element[1], parent=self, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        if self.style.displaystyle:
            ynum = self.units_to_points(
                -self.font.math.consts.fractionNumeratorDisplayStyleShiftUp)
            ydenom = self.units_to_points(
                self.font.math.consts.fractionDenominatorDisplayStyleShiftDown)
        else:
            ynum = self.units_to_points(
                -self.font.math.consts.fractionNumeratorShiftUp)
            ydenom = self.units_to_points(
                self.font.math.consts.fractionDenominatorShiftDown)

        denombox = self.denominator.bbox
        numbox = self.numerator.bbox

        if ynum + numbox.ymin < 0:
            ynum += numbox.ymin + self.units_to_points(
                self.font.math.consts.fractionNumeratorGapMin)
        if ydenom - denombox.ymax < 0:
            ydenom -= ydenom - denombox.ymax + self.units_to_points(
                self.font.math.consts.fractionDenominatorGapMin)

        x = 0.
        if (leftsibling := self.leftsibling()):
            if leftsibling.mtag == 'mfrac':
                x = self.ems_to_pts(space_ems('verythinmathspace'))
            else:
                x = self.ems_to_pts(space_ems('thinmathspace'))

        width = max(numbox.xmax, denombox.xmax)
        xnum = x + (width - (numbox.xmax - numbox.xmin))/2
        xdenom = x + (width - (denombox.xmax - denombox.xmin))/2
        self.nodes.append(self.numerator)
        self.nodes.append(self.denominator)
        self.nodexy.append((xnum, ynum))
        self.nodexy.append((xdenom, ydenom))

        linethick = self.units_to_points(self.font.math.consts.fractionRuleThickness)
        if 'linethickness' in self.element.attrib:
            lt = self.element.get('linethickness', '')
            try:
                linethick = topoints(lt, self.glyphsize)
            except ValueError:
                linethick = {'thin': linethick * .5,
                             'thick': linethick * 2}.get(lt, linethick)

        bary = self.units_to_points(-self.font.math.consts.axisHeight)
        self.nodes.append(HLine(width, linethick, style=self.style, **kwargs))
        self.nodexy.append((x, bary))

        # Calculate/cache bounding box
        xmin = 0
        xmax = x + max(numbox.xmax, denombox.xmax)
        xmax += self.ems_to_pts(space_ems('thinmathspace'))
        ymin = (-ydenom) + denombox.ymin
        ymax = (-ynum) + numbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)
