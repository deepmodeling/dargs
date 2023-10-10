Use with DP-GUI
===============

Developers can export an :class:`Argument <dargs.Argument>` to `DP-GUI <https://github.com/deepmodeling/dpgui>`_ for users, by adding a :code:`dpgui` entry point to `pyproject.toml`:

.. code-block:: toml

   [project.entry-points."dpgui"]
    "Test Argument" = "dargs.sphinx:_test_argument"

where `_test_argument` returns an :class:`Argument <dargs.Argument>` or a list of :class:`Argument <dargs.Argument>`, and :code:`"Test Argument"` is its name that can be any string.

Users can install the `dpgui` Python package via `pip` and serve the DP-GUI instance using the `dpgui` command line:

.. code-block:: sh

    pip install dpgui
    dpgui

The served DP-GUI will automatically load all templates from the :code:`dpgui` entry point.
