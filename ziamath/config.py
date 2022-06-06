''' Global configuration options '''
from ziafont import config as zfconfig


class Config:
    ''' Global configuration options for Ziamath
    
        Attributes
        ----------
        minsizefraction: Smallest allowed text size, as fraction of
            base size, for text such as subscripts and superscripts
        debug: Debug mode, draws bounding boxes around <mrows>
        svg2: Use SVG2.0. Disable for better browser compatibility,
            at the expense of SVG size
        precision: SVG decimal precision for coordinates
    '''
    minsizefraction: float = .3
    debug: bool = False
    
    @property
    def svg2(self) -> bool:
        return zfconfig.svg2
    
    @svg2.setter
    def svg2(self, value: bool) -> None:
        zfconfig.svg2 = value

    @property
    def precision(self) -> float:
        return zfconfig.precision
    
    @precision.setter
    def precision(self, value: float) -> None:
        zfconfig.precision = value

    
config = Config()