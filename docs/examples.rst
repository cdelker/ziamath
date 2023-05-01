.. _examples:

Examples
========


.. jupyter-execute::
    :hide-code:

    import ziamath as zm
    def loadmath(fname):
        with open(fname, 'r') as f:
            xml = f.read()
        return zm.Math(xml)


Supported MathML Elements
-------------------------

Superscripts and Subscripts <msup>, <msub>, <msubsup>
*****************************************************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exB1.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exB1.xml
  :language: XML

.. raw:: html

   </details>
   
------------


Square Root <msqrt>
*******************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exB2.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exB2.xml
  :language: XML

.. raw:: html

   </details>
   
------------


N-root <mroot>
**************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exB3.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exB3.xml
  :language: XML

.. raw:: html

   </details>
   
------------

Fractions <mfrac>
*****************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exB4.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exB4.xml
  :language: XML

.. raw:: html

   </details>
   
------------

Over/Under <mover>, <munder>
****************************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exB5.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exB5.xml
  :language: XML

.. raw:: html

   </details>
   
------------

Fenced <mfenced>
****************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exB6.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exB6.xml
  :language: XML

.. raw:: html

   </details>
   
------------


Tables <mtable>
***************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exB7.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exB7.xml
  :language: XML

.. raw:: html

   </details>
   
------------



Enclosures <menclose>
---------------------

notation="box"
**************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exA1.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exA1.xml
  :language: XML

.. raw:: html

   </details>
   
------------

notation="updiagonalstrike downdiagonalstrike"
**********************************************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exA2.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exA2.xml
  :language: XML

.. raw:: html

   </details>

------------



Color and Highlight attributes
------------------------------

mathcolor
*********

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exA3.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exA3.xml
  :language: XML

.. raw:: html

   </details>

------------

mathbackground
**************

|

.. jupyter-execute::
    :hide-code:
    
    loadmath('mml/exA4.xml')

|

.. raw:: html

   <details>
   <summary><a>MathML</a></summary>

.. literalinclude:: mml/exA4.xml
  :language: XML

.. raw:: html

   </details>

----------


Latex
-----

.. jupyter-execute::

    zm.Latex(r'x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}')

|


.. jupyter-execute::

    zm.Latex(r'i \hbar \frac{\partial}{\partial t}\Psi(\mathbf{r},t) = \hat H \Psi(\mathbf{r},t)')

|


.. jupyter-execute::

    zm.Latex(r'\Delta v = v_e \, \ln \frac{m_0}{m_f} = I_{sp} \, g_0 \, \ln \frac{m_0}{m_f}')
