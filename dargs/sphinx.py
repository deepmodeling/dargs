"""Sphinx extension.

To enable dargs Sphinx extension, add :mod:`dargs.sphinx` to the extensions of conf.py:

.. code-block:: python

   extensions = [
       'dargs.sphinx',
   ]


Then `dargs` directive will be added:

.. code-block:: rst

    .. dargs::
       :module: dargs.sphinx
       :func: _test_argument

where `_test_argument` returns an :class:`Argument <dargs.Argument>`. A :class:`list` of :class:`Argument <dargs.Argument>` is also accepted. 
"""
import sys

from docutils import nodes
from docutils.parsers.rst import Directive, Parser
from docutils.parsers.rst.directives import unchanged
from docutils.statemachine import ViewList
from docutils.frontend import OptionParser
from docutils.utils import new_document

from .dargs import Argument, Variant

def parse_rst(text: str) -> nodes.document:
    """Parse rst texts to nodes.

    Parameters
    ----------
    text : str
        raw rst texts

    Returns
    -------
    nodes.document
        nodes
    """
    parser = Parser()
    components = (Parser,)
    settings = OptionParser(components=components).get_default_values()
    document = new_document('', settings=settings)
    parser.parse(text, document)
    return document


class DargsDirective(Directive):
    """dargs directive"""
    has_content = True
    option_spec = dict(
        module=unchanged,
        func=unchanged,
    )


    def run(self):
        if 'module' in self.options and 'func' in self.options:
            module_name = self.options['module']
            attr_name = self.options['func']
        else:
            raise self.error(':module: and :func: should be specified')

        try:
            mod = __import__(module_name, globals(), locals(), [attr_name])
        except ImportError:
            raise self.error(f'Failed to import "{attr_name}" from "{module_name}".\n{sys.exc_info()[1]}')

        if not hasattr(mod, attr_name):
            raise self.error(('Module "%s" has no attribute "%s"\n' 'Incorrect argparse :module: or :func: values?') % (module_name, attr_name))
        func = getattr(mod, attr_name)
        arguments = func()

        if not isinstance(arguments, (list, tuple)):
            arguments = [arguments]

        items = []
        for argument in arguments:
            if not isinstance(argument, (Argument, Variant)):
                raise RuntimeError("The function doesn't return Argument")
            rst = argument.gen_doc(make_anchor=True, make_link=True)
            items.extend(parse_rst(rst))

        return items


def setup(app):
    """Setup sphinx app."""
    app.add_directive('dargs', DargsDirective)
    return {'parallel_read_safe': True}


def _test_argument() -> Argument:
    """This internal function is used to generate docs of dargs."""
    return Argument(name="test", dtype=str, doc="This argument is only used to test.")
