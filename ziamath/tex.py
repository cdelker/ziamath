''' Latex to MathML interface '''
import re
import latex2mathml.tokenizer  # type: ignore
import latex2mathml.commands  # type: ignore
from latex2mathml.converter import convert  # type: ignore

from .config import config


def declareoperator(name: str) -> None:
    r''' Declare a new operator name, similar to Latex ``\DeclareMathOperator`` command.

        Args:
            name: Name of operator, should start with a ``\``.
                Example: ``declareoperator(r'\myfunc')``
    '''
    latex2mathml.commands.FUNCTIONS = latex2mathml.commands.FUNCTIONS + (name,)


def tex2mml(tex: str, inline: bool = False) -> str:
    ''' Convert Latex to MathML. Do some hacky preprocessing to work around
        some issues with generated MathML that ziamath doesn't support yet.
    '''
    tex = re.sub(r'\\binom{(.+?)}{(.+?)}', r'\\left( \1 \\atop \2 \\right)', tex)
    # latex2mathml bug requires space after mathrm
    tex = re.sub(r'\\mathrm{(.+?)}', r'\\mathrm {\1}', tex)
    tex = tex.replace('||', '‖')
    if config.decimal_separator == ',':
        # Replace , with {,} to remove right space
        # (must be surrounded by digits)
        tex = re.sub(r'([0-9]),([0-9])', r'\1{,}\2', tex)

    mml = convert(tex, display='inline' if inline else 'block')

    # Replace some operators with "stretchy" variants
    mml = re.sub(r'<mo>&#x0005E;', r'<mo>&#x00302;', mml)  # widehat
    mml = re.sub(r'<mo>&#x0007E;', r'<mo>&#x00303;', mml)  # widetilde
    return mml
