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


from typing import List, Union, Dict, Any, Iterable, Optional


class Argument:

    def __init__(self, 
            name: str,
            dtype: Union[None, type, Iterable[type]],
            sub_fields: Optional[List["Argument"]] = None,
            sub_variants: Optional[List["Variant"]] = None,
            repeat: bool = False,
            optional: bool = False,
            default: Any = None, # for now it is just a tag, no real use
            doc: str = ""):
        self.name = name
        self.dtype = dtype
        self.sub_fields = sub_fields if sub_fields is not None else []
        self.sub_variants = sub_variants if sub_variants is not None else []
        self.repeat = repeat
        self.optional = optional
        self.default = default
        self.doc = doc
        # handle the format of dtype, makeit a tuple
        self.reorg_dtype()

    def reorg_dtype(self):
        if isinstance(self.dtype, type) or self.dtype is None:
            self.dtype = [self.dtype]
        # remove duplicate
        self.dtype = set(self.dtype)
        # check conner cases
        if self.sub_fields and self.repeat:
            self.dtype.add(list)
        if self.sub_fields and not self.repeat or self.sub_variants:
            self.dtype.add(dict)
        if None in self.dtype:
            self.dtype.remove(None)
            self.dtype.add(type(None))
        # and make it compatible with `isinstance`
        self.dtype = tuple(self.dtype)

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
            self._check_subvariant(item)


class Variant:

    def __init__(self, 
            flag_name: str,
            choices: List["Argument"],
            optional: bool = False,
            default_tag: str = "", # this is indeed necessary in case of optional
            doc: str = ""):
        self.flag_name = flag_name
        self.choice_dict = {}
        self.add_choice(*choices)
        self.optional = optional
        self.default_tag = default_tag
        self.doc = doc

    def add_choice(self, *choices: Argument):
        # choices is a list of arguments 
        # whose name is treated as the switch tag
        # we convert it into a dict for better reference
        # and avoid duplicate tags
        for arg in choices:
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

        