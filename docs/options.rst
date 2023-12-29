Options
=======

.. jupyter-execute::
    :hide-code:

    import ziamath as zm


Image Formats
-------------

Drawing on an existing SVG
**************************

To draw math expressions on an existing SVG, create the SVG XML structure using an `XML Element Tree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_.
Then use :py:meth:`ziamath.zmath.Math.drawon`, or :py:meth:`ziamath.zmath.Text.drawon`, with the x and y position and svg to draw on:

.. jupyter-execute::

    from IPython.display import SVG
    from xml.etree import ElementTree as ET

    svg = ET.Element('svg')
    svg.set('width', '200')
    svg.set('height', '100')
    svg.set('xmlns', 'http://www.w3.org/2000/svg')
    svg.set('viewBox', f'0 0 100 100')
    circ = ET.SubElement(svg, 'circle')
    circ.set('cx', '20')
    circ.set('cy', '25')
    circ.set('r', '25')
    circ.set('fill', 'orange')

    myequation = zm.Latex(r'\int_0^1 f(x) \mathrm{d}x', size=18)
    myequation.drawon(svg, 50, 45)

    SVG(ET.tostring(svg))

|

Raster Image Formats
********************

Ziamath only outputs SVG format, but other image formats may be obtained using other Python libraries.
`Cairosvg <https://cairosvg.org/>`_ can be used to convert to PNG, for example:

.. code-block:: python

    import cairosvg
    expr = zm.Latex('$x^2 + y^2$')
    pngbytes = cairosvg.svg2png(expr.svg())

|

Customization
-------------


Declaring Operators
*******************

To declare a new math operator, use :py:meth:`ziamath.tex.declareoperator`. This works similar to LaTeX's DeclareMathOperator to allow custom function names typeset as functions instead of identifiers.

Decimal Separator
*****************

For regions that use a comma as the decimal separator, set `ziamath.config.decimal_separator`.
This removes the space after the commas between two digits, by treating it as if it were enclosed in braces, such as `1{,}0`. Only used for Latex expressions.

.. jupyter-execute::

    zm.Latex('1,2')
    
.. jupyter-execute::

    zm.config.decimal_separator = ','
    display(zm.Latex('1,2'))

|


Configuration Options
---------------------

Global configuration options can be set in the `ziamath.config` object.

Math Style
**********

The default math style can be set with the following parameters. These settings may be overridden by arguments to `zm.Math` or `zm.Latex`.

.. code-block:: python

    zm.config.math.mathfont   # Path to math font file
    zm.config.math.variant    # 'serif', 'sans', 'bold', 'script', etc.
    zm.config.math.fontsize   # size in points
    zm.config.math.color = 'black'      # css-supported color
    zm.config.math.background = 'none'  # css-supported color


Text Style
**********

The default style of plain text in `zm.Text` instances may be set using the following configuration parameters:

.. code-block:: python

    zm.config.text.textfont   # Path to font file
    zm.config.text.variant    # 'serif', 'sans', 'bold', 'script', etc.
    zm.config.text.fontsize   # size in points
    zm.config.text.color      # css-supported color
    zm.config.text.linespacing  # Line spacing multiplier


SVG Version Compatibility
*************************

Some SVG renderers, including recent versions of Inkscape and some OS built-in image viewers, are not fully compatible with the SVG 2.0 specification.
Set the `ziamath.config.svg2` parameter to `False` for better compatibility. This may result in larger file sizes
as each glyph is included as its own <path> element rather than being reused with <symbol> and <use> elements.

If your images looks like all the symbols are stacked on top of each other, try setting this option to False.

.. code-block:: python

    zm.config.svg2 = False



Decimal Precision
*****************

The decimal precision of coordinates in SVG tags can be set using ziafont.config.precision. Lower precision saves space in the SVG string, but may reduce quality of the image.

.. code-block:: python

    zm.config.precision = 2

Minimum Fraction Size
*********************

Fractions, superscripts, and other elements are reduced in size depending on the depth of the element. By default, the smallest allowable font size is 30 \% of the original font size.
This fraction can be changed using `zm.config.minsizefraction`

.. code-block:: python

    zm.config.minsizefraction = 0.5  # Only allow sizes to be reduced in half from the base font size

|

Command Line
------------

Ziamath may be accessed from the command line, reading input from a file with

.. code-block:: bash

    python -m ziamath inputfile.txt

Or reading stdin:

.. code-block:: bash

    echo "x^2 + y^2" | python -m ziamath

Run `python -m ziamath --help` to show all the options. It attempts to automatically determine whether
the input is MathML or Latex, but the `--latex` argument may be provided to force Latex mode.


|

Limitations
-----------

While the most common features are supported, Ziamath is not a comprehensive implementation of the MathML or MathML Core specification.
At this time, unsupported elements and attributes inculde:

- Elementary Math Layout: <mstack>, <msrow>, <msline>, <mlongdiv>, etc.
- Some table alignment tags and attributes, such as borders, <mlabeledtr>, and <maligngroup>
- Right-to-left text


Latex support is provided by `latex2mathml <https://pypi.org/project/latex2mathml/>`_.