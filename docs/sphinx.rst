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

where `_test_argument` returns an :class:`Argument <dargs.Argument>`. The documentation will be rendered as:

.. dargs::
   :module: dargs.sphinx
   :func: _test_argument

A :class:`list` of :class:`Argument <dargs.Argument>` is also accepted.

.. dargs::
   :module: dargs._test
   :func: test_arguments

To write Markdown files with `MyST-Parser <https://github.com/executablebooks/MyST-parser>`_, one can use:

.. code-block:: markdown

    ```{eval-rst}
    .. dargs::
       :module: dargs.sphinx
       :func: _test_argument
    ```

Cross-referencing Arguments
---------------------------

Both the following ways will create a cross-reference to the argument:

.. code-block:: rst

   Both :dargs:argument:`this <test/test_argument>` and :ref:`this <test/test_argument>` will create a cross-reference to the argument!

It will be rendered as:

   Both :dargs:argument:`this <test/test_argument>` and :ref:`this <test/test_argument>` will create a cross-reference to the argument!


Index page
----------

The arguments will be added into the :ref:`genindex` page. See :ref:`test_argument <test/test_argument>` in the :ref:`genindex` page.
