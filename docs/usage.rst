Usage
=====

Installation
------------

Ziamath can be installed using pip:

.. code-block:: bash

    pip install ziamath


Ziamath depends only on two pure-Python packages: `Ziafont <https://ziafont.readthedocs.io>`_, for reading TTF/OTF font files, and `latex2mathml <https://pypi.org/project/latex2mathml/>`_ for parsing Latex math expressions.

|

Drawing Equations
-----------------

The :py:class:`ziamath.zmath.Math` class processes and draws a given MathML <math> element.
Set up a `Math` object by providing a `MathML <https://www.w3.org/TR/MathML3/>`_ string:

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

In Jupyter notebooks, the `Math` instance will be rendered in the cell's output.
The raw SVG is obtained using :py:meth:`ziamath.zmath.Math.svg`, for SVG as a string:

.. jupyter-execute::

    eqn.svg()[:80]  # Only show first 80 characters...

or :py:meth:`ziamath.zmath.Math.svgxml` for the SVG in an XML ElementTree.

.. jupyter-execute::

    eqn.svgxml()


The `Math` class takes optional parameters for font file name and font size.
The font file must be math-enabled, with an embedded 'MATH' table.

|

Drawing Latex
-------------
 
To render a math expression in Latex format, create the Math object using :py:meth:`ziamath.zmath.Latex`:

.. jupyter-execute::

    zm.Latex(r'c = \pm \sqrt{a^2 + b^2}')

The Latex class inherits from the Math class. Be sure to use raw strings (prefixed with an `r`) so that slashes for Latex commands 
are interpreted as slashes and not string escape characters.


|


Display Mode and Inline Mode
****************************

Latex math is drawn in display (block) mode by default. To render inline (text) mode, set the `inline` parameter to `True`.

.. jupyter-execute::

    zm.Latex(r'\sum_a^b', inline=False)  # Default display mode

.. jupyter-execute::

    zm.Latex(r'\sum_a^b', inline=True)  # Inline mode


|


Mixed Math and Text
-------------------

:py:class::py:class:`ziamath.zmath.Text` renders mixed math and text into a single <svg> element, drawing both math
and text characters as SVG paths.
It takes a string input with math expressions enclosed between single dollar signs $..$ for inline-mode math, and double dollar signs $$..$$ for block or display style math.
Different fonts may be used for the plain text and math portions.

.. jupyter-execute::

    zm.Text(
        r'''The volume of a sphere is
    $V = \frac{4}{3}\pi r^3$
    or in terms of diameter,
    $ V = \frac{\pi d^3}{6}$.
    ''', halign='center')

The `textfont` argument may be the path to a font file, or name of a font-family such as "sans", "sans bold", etc.
The `mathstyle` provides styling to the math expressions.

Text objects support rotation (in degrees) and color (CSS named color or hex color value):

.. jupyter-execute::

    zm.Text('$\\sqrt{a}$', rotation=30, color='mediumslateblue')

