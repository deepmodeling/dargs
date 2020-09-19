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


from typing import List, Union, Dict, Any, Iterable
from dataclasses import dataclass, field


@dataclass
class Argument:
    name: str
    dtype: Union(type, Iterable[type])
    sub_fields: List["Argument"] = field(default_factory=list)
    sub_variants: List["Variant"] = field(default_factory=list)
    repeat: bool = False
    optional: bool = False
    default: Any = None # for now it is just a tag, no real use
    doc: str = ""

    def __post_init__(self):
        if isinstance(self.dtype, type):
            self.dtype = [self.dtype]
        if self.sub_fields and self.repeat:
            self.dtype = [*self.dtype, list]
        if self.sub_fields and not self.repeat or self.sub_variants:
            self.dtype = [*self.dtype, dict]
        # remove duplicate and make it compatible with `isinstance`
        self.dtype = tuple(set(self.dtype))

    def check(self, argdict: dict):
        # first, check existence of a key
        # then, take out the vaule and check its type
        self._check_exist(argdict)
        if self.name in argdict:
            # this is the key step that we traverse into the tree
            self.check_value(argdict[self.name])

    def check_value(self, value: Any):
        # this is not private, and can be called directly
        # in the condition where there is no leading key
        self._check_dtype(value)
        if isinstance(value, dict):
            self._check_subfield(value)
            self._check_subvariant(value)
        if isinstance(value, list) and self.repeat:
            self._check_repeat(value)
            
    def _check_exist(self, argdict: dict):
        if self.optional is True:
            return
        if self.name not in argdict:
            raise KeyError(f"Key `{self.name}` is required "
                            "in arguments but not found")

    def _check_dtype(self, value: Any):
        if not isinstance(value, self.dtype):
            raise TypeError(f"Key `{self.name}` gets wrong value type: "
                            f"requires: {self.dtype} but gets {type(value)}")

    def _check_subfield(self, value: dict):
        assert isinstance(value, dict)
        for subarg in self.sub_fields:
            subarg.check(value)

    def _check_subvariant(self, value: dict):
        assert isinstance(value, dict)
        for subvrnt in self.sub_variants:
            subvrnt.check(value)

    def _check_repeat(self, value: list):
        assert isinstance(value, list) and self.repeat
        for item in value:
            self._check_subfield(item)


@dataclass
class Variant:
    flag_name: str
    choices: List["Arguments"] = field(default_factory=list)
    optional: bool = False
    default_tag: str = "" # this is indeed necessary in case of optional
    doc: str = ""

    def __post_init__(self):
        # choices is a list of arguments 
        # whose name is treated as the switch tag
        # we convert it into a dict for better reference
        # and avoid duplicate tags
        self.choice_dict = {}
        for arg in self.choices:
            tag = arg.name
            if tag in self.choice_dict:
                raise ValueError(f"duplicate tag `{tag}` appears in "
                                 f"variant with flag `{self.flag_name}`")
            self.choice_dict[tag] = arg

    def check(self, argdict: dict):
        choice = self._load_choice(argdict)
        # here we use check_value to flatten the tag
        choice.check_value(argdict)

    def _load_choice(self, argdict: dict) -> Argument:
        if self.flag_name in argdict:
            tag = argdict[self.flag_name]
            return self.choice_dict[tag]
        elif self.optional:
            return self.choice_dict[self.default_tag]
        else:
            raise KeyError(f"Key `{self.flag_name}` is required "
                            "to choose variant but not found.")

        