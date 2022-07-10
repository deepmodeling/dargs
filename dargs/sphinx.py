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

from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import unchanged
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode

from .dargs import Argument, Variant


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

        for argument in arguments:
            if not isinstance(argument, (Argument, Variant)):
                raise RuntimeError("The function doesn't return Argument")
            rst = argument.gen_doc(make_anchor=True, make_link=True, use_sphinx_domain=True)
            self.state_machine.insert_input(rst.split("\n"), "%s:%s" %(module_name, attr_name))
        return []


class DargsObject(ObjectDescription):
    """dargs::argument directive.
    
    This directive creates a signature node for an argument.
    """
    option_spec = dict(
        path=unchanged,
    )

    def handle_signature(self, sig, signode):
        signode += addnodes.desc_name(sig, sig)
        return sig

    def add_target_and_index(self, name, sig, signode):
        path = self.options['path']
        targetid = "%s:%s" % (self.objtype, path)
        if targetid not in self.state.document.ids:
            signode['names'].append(targetid)
            signode['ids'].append(targetid)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            # for cross-references
            inv = self.env.domaindata['dargs']['arguments']
            if targetid in inv:
                self.state.document.reporter.warning(
                    'Duplicated argument "%s" described in "%s".' %
                    (targetid, self.env.doc2path(inv[targetid][0])), line=self.lineno)
            inv[targetid] = (self.env.docname, self.objtype)

        self.indexnode['entries'].append(('pair', u'%s ; %s (%s) ' % (name, path, self.objtype.title()), targetid, 'main', None))


class DargsDomain(Domain):
    """Dargs domain.
    
    Includes:
    - dargs::argument directive
    - dargs::argument role
    """
    name = 'dargs'
    label = 'dargs'
    object_types = {
        'argument': ObjType('argument', 'argument'),
    }
    directives = {
        'argument': DargsObject,
    }
    roles = {
        'argument': XRefRole(),
    }

    initial_data = {
        'arguments': {},  # fullname -> docname, objtype
    }

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        """Resolve cross-references."""
        targetid = '%s:%s' % (typ, target)
        obj = self.data['arguments'].get(targetid)
        if obj is None:
            return None
        return make_refnode(builder, fromdocname, obj[0], targetid,
                            contnode, target)


def setup(app):
    """Setup sphinx app."""
    app.add_directive('dargs', DargsDirective)
    app.add_domain(DargsDomain)
    return {'parallel_read_safe': True}


def _test_argument() -> Argument:
    """This internal function is used to generate docs of dargs."""
    doc_test = "This argument/variant is only used to test."
    return Argument(name="test", dtype=str, doc=doc_test,
        sub_fields=[
            Argument("test_argument", dtype=str, doc=doc_test, default="test"),
        ],
        sub_variants=[
            Variant("test_variant", doc=doc_test,
                choices=[
                    Argument("test_variant_argument", dtype=str, doc=doc_test),
                ],
            ),
        ],
    )
