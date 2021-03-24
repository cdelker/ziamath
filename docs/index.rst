Ziamath
=======

Ziamath renders MathML or LaTeX Math expressions as SVG paths. Does not require a Latex installation, nor rely on any third party services, but rather uses math-enabled fonts, such as `STIXTwoMath-Regular <https://www.stixfonts.org/>`_ which comes included with Ziamath
for use by default. The resulting SVGs are drawn entirely with <path> elements, so the image does not depend on
having the font available.


Example
-------

To render from MathML:

.. jupyter-execute::

    import ziamath as zm
    zm.Math(
    '''<mrow>
         <mi> y </mi>
         <mo> = </mo>
         <mi> f </mi>
         <mo> &ApplyFunction; </mo>
         <mrow>
           <mo> ( </mo>
           <mi> x </mi>
           <mo> ) </mo>
         </mrow>
       </mrow>''')

|

To render from Latex:

.. jupyter-execute::

    zm.Math.fromlatex(r'\frac{1}{1-x^2}')



Installation
------------

Ziamath can be installed using pip:

.. code-block:: bash

    pip install ziamath


Ziamath natively draws MathML. For Latex support, the `latex2mathml <https://pypi.org/project/latex2mathml/>`_ package is used to convert the Latex into MathML first.
It can be installed along with ziamath:

.. code-block:: bash

    pip install ziamath[latex]


Ziamath depends on its sister package, `Ziafont <https://ziafont.readthedocs.io>`_, for reading TTF font files.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage.rst
   test.rst
