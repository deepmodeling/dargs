r"""
Some (ocaml) pseudo-code here to show the type structure::

    type args = item list
    and  item = 
           | Field of {key: str; doc: str; value: data}
           | Union of {switch: str; choices: (str * args) list}
    and  data = 
           | Arg of dtype
           | Node of args
           | Repeat of args

In actual implementation, ``args`` is a class that has two attributes, 
``fields: Dict[str, Tuple[str, data]]`` and 
``unions: Dict[str, List[Tuple[str, args]]]``
that correspond to the ``item`` type. So this layer is flattened.
On the otherhand, ``data`` type is still implemented by inherence
from a base type to three variants.
"""

import typing

