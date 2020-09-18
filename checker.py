r"""
Some (ocaml) pseudo-code here to show the intended type structure::
           
    type args = {key: str; value: data; optional: bool; doc: str} list
    and  data = 
           | Arg of dtype
           | Node of args
           | Repeat of args
           | Variant of (str * args) list

In actual implementation, We flatten this structure into on tree-like class
`Argument` with (optional) attribute `dtype`, `sub_fields`, `repeat` and 
`sub_variants` to mimic the union behavior in the type structure.

Due to the complexity of *Variant* structure, it is implemented into a 
separate class `Variant` so that multiple choices can be handled correctly.
We also need to pay special attention to flat the keys of its choices.
"""


from typing import List, Union, Dict, Any, Union
from dataclasses import dataclass, field


@dataclass
class Argument:
    name: str
    dtype: Union(type, List[type])
    sub_fields: List["Argument"] = field(default_factory=list)
    sub_variants: List["Variant"] = field(default_factory=list)
    repeat: bool = False
    optional: bool = False
    default: Any = None
    doc: str = ""


@dataclass
class Variant:
    flag_name: str
    choices: Dict[str, "Arguments"] = field(default_factory=dict)
    optional: bool = False
    default: str = ""
    doc: str = ""
