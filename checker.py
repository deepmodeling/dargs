r"""
Some (ocaml) pseudo-code here to show the intended type structure::

    type args = item list
    and  item = 
           | Field of {key: str; value: data; optional: bool; doc: str}
           | Variant of {flag: str; choices: (str * args * str) list; 
                         optional: bool; default: str; doc: str}
    and  data = 
           | Arg of dtype
           | Node of args
           | Repeat of args

In actual implementation, *args* is a class that has two attributes, 
``fields: Dict[str, AbstractData]`` and ``variants: Dict[str, TaggedUnion]``
that correspond to the *item* type. So this layer is flattened.

``AbstractData`` class is a combine of *value*, *optional* and *doc*
of *Field* record and is inheritanced by three variants of the *data* type.
This gives possibility to add more data format.

``TaggedUnion`` class is a combine of *choices*, "optional*, *default*
and *doc* of *Variant* record. It is used to handle the multiple choices 
condition in the argument dict.
"""


from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Arguments:
    fields: Dict[str, "AbstractData"] = field(default_factory=dict)
    variants: Dict[str, "TaggedUnion"] = field(default_factory=dict)


@dataclass
class TaggedUnion:
    choices: Dict[str, "Arguments"] = field(default_factory=dict)
    optional: bool = False
    default: str = ""
    doc: str = ""


class AbstructData(ABC):
    @abstractmethod
    def check_value(value: Any):
        pass


@dataclass
class ArgData(AbstructData):
    dtype: List[type]
    optional: bool = False
    default: Any = None
    doc: str = ""


@dataclass
class NodeData(AbstructData):
    args: Arguments
    optional: bool = False
    doc: str = ""


@dataclass
class RepeatData(AbstructData):
    unitargs: Arguments
    optional: bool = False
    doc: str = ""
