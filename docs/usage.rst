Usage
=====

Installation
------------

Ziamath can be installed using pip:

.. code-block:: bash

    pip install ziamath


Ziamath natively works with MathML. For Latex support, the `latex2mathml <https://pypi.org/project/latex2mathml/>`_ package is used to convert the Latex into MathML first.
It can be installed along with ziamath:

.. code-block:: bash

    pip install ziamath[latex]


Ziamath depends on its sister package, `Ziafont <https://ziafont.readthedocs.io>`_, for reading TTF font files.

|

Drawing Equations
-----------------

The :py:class:`ziamath.zmath.Math` class processes and draws a MathML <math> element.
The Math class has a Jupyter representation that shows the SVG
image as the output of a cell.
To render a `MathML <https://www.w3.org/TR/MathML3/>`_ string:

.. jupyter-execute::

    import ziamath as zm

    eqn = zm.Math('''
                  <mrow>
                      <msup>
                          <mi>x</mi>
                          <mn>2</mn>
                      </msup>
                  </mrow>
                  ''')
    eqn

To get the raw SVG, create the Math object, then use :py:meth:`ziamath.zmath.Math.svg` for the SVG as a string:

.. jupyter-execute::

    eqn.svg()[:80]  # Only show first 80 characters...

or :py:meth:`ziamath.zmath.Math.svgxml` for an XML ElementTree.

.. jupyter-execute::

    eqn.svgxml()


The Math class takes optional parameters for font file name and font size.
The font file must be math-enabled, with an embedded 'MATH' table.

|

Drawing Latex
-------------
 
To render a math expression in Latex format, create the Math object using :py:meth:`ziamath.zmath.Math.fromlatex`:

.. jupyter-execute::

    zm.Math.fromlatex(r'c = \pm \sqrt{a^2 + b^2}')

|

Mixed Math and Text
-------------------

:py:meth:`ziamath.zmath.Math.fromlatextext` converts a string expression with one or more
embedded math expressions enclosed within $..$. into a single MathML <math> element
with the plain text placed within <mtext> elements. This method works for single line
math and text expressions.

.. jupyter-execute::

    zm.Math.fromlatextext(r'The volume of a sphere is $V = \frac{4}{3}\pi r^3$.', textstyle='sans')

The `textstyle` argument provides styling to the plain text, and `mathstyle` provides styling
to the math expressions. Both arguments may be an allowable MathML "mathvariant" attribute, such as 'sans', 'serif', 'italic', 'bold', 'sans-bold', etc.

Text Objects
------------

Another option for mixed math and text is the :py:class:`ziamath.zmath.Text` class.
It takes a string, which may contain multiple lines and math expressions enclosed in $..$,
and draws directly to SVG. The text is drawn directly; no <mtext> elements are used and the MathML is not available.
Different fonts may be used for the plain text and math portions.

.. jupyter-execute::

    zm.Text(
        r'''The volume of a sphere is
    $V = \frac{4}{3}\pi r^3$
    or in terms of diameter,
    $ V = \frac{\pi d^3}{6}$.
    ''', halign='center')

Text objects support rotation:

.. jupyter-execute::

    zm.Text('$\\sqrt{a}$', rotation=30)


|

Drawing on an existing SVG
--------------------------

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

    myequation = zm.Math.fromlatex(r'\int_0^1 f(x) \mathrm{d}x', size=18)
    myequation.drawon(svg, 50, 45)

    SVG(ET.tostring(svg))

|



Other image formats
-------------------

Ziamath only outputs SVG format, but other image formats may be obtained using other Python libraries.
`Cairosvg <https://cairosvg.org/>`_ can be used to convert to PNG, for example:

.. code-block:: python

    import cairosvg
    expr = zm.Math.fromlatextext('$x^2 + y^2$')
    pngbytes = cairosvg.svg2png(expr.svg())

|

Configuration Options
---------------------

Global configuration options can be set in the `ziamath.config` object.

SVG Version Compatibility
*************************

Some SVG renderers, including recent versions of Inkscape and some OS built-in image viewers, are not fully compatible with the SVG 2.0 specification.
Set the `ziamath.config.svg2` parameter to `False` for better compatibility. This may result in larger file sizes
as each glyph is included as its own <path> element rather than being reused with <symbol> and <use> elements.

.. code-block:: python

    zm.config.svg2 = False
    zm.Math.fromlatextext('$x^2 + y^2$')

Decimal Precision
*****************

The decimal precision of coordinates in SVG tags can be set using ziafont.config.precision. Lower precision saves space in the SVG string, but may reduce quality of the image.

.. code-block:: python

    zm.config.precision = 2


|


Command Line
------------

Ziamath may be accessed from the command line, reading input from a file with

.. code-block:: bash

    python -m ziamath inputfile.txt

Or reading stdin (with LaTeX input):

.. code-block:: bash

    echo "x^2 + y^2" | python -m ziamath --latex

Run `python -m ziamath --help` to show all the options.


|

Limitations
-----------

Not every MathML element is implemented at this time.
Unsupported elements and attributes inculde:

- <mstyle>
- <ms>
- <mglyph>
- <merror>
- <mmultiscripts>
- <mlabeledtr>
- scriptlevel attribute
- table alignment attributes

