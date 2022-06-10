Use with Sphinx
===============

Add :mod:`dargs.sphinx` to the extensions of conf.py:

.. code-block:: python

   extensions = [
       'dargs.sphinx',
   ]


Then `dargs` directive will be enabled:

.. code-block:: rst

    .. dargs::
       :module: dargs.sphinx
       :func: _test_argument

where `_test_argument` returns an :class:`Argument <dargs.Argument>`. A :class:`list` of :class:`Argument <dargs.Argument>` is also accepted. The documentation will be rendered as:

.. dargs::
   :module: dargs.sphinx
   :func: _test_argument
