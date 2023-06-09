from .mathtable import MathTable
from .styles import styledchr, styledstr
from .zmath import Math, Latex, Text, declareoperator
from .config import config

__version__ = '0.8.1'


declareoperator(r'\tg')
declareoperator(r'\ctg')
declareoperator(r'\arcctg')
declareoperator(r'\arctg')
declareoperator(r'\arg')
declareoperator(r'\cotg')
declareoperator(r'\sh')
declareoperator(r'\ch')
declareoperator(r'\cth')
declareoperator(r'\th')
