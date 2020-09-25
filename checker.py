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


from typing import Union, Any, List, Iterable, Optional
from textwrap import wrap, fill, indent


INDENT = "    " # doc is indented by four spaces

class Argument:

    def __init__(self, 
            name: str,
            dtype: Union[None, type, Iterable[type]],
            sub_fields: Optional[Iterable["Argument"]] = None,
            sub_variants: Optional[Iterable["Variant"]] = None,
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

    def __eq__(self, other: "Argument") -> bool:
        # do not compare doc and default
        # since they do not enter to the type checking
        fkey = lambda f: f.name
        vkey = lambda v: v.flag_name
        return (self.name == other.name 
            and set(self.dtype) == set(other.dtype)
            and sorted(self.sub_fields, key=fkey) == sorted(other.sub_fields, key=fkey)
            and sorted(self.sub_variants, key=fkey) == sorted(other.sub_variants, key=fkey)
            and self.repeat == other.repeat
            and self.optional == other.optional)

    def reorg_dtype(self):
        if isinstance(self.dtype, type) or self.dtype is None:
            self.dtype = [self.dtype]
        # remove duplicate
        self.dtype = set(self.dtype)
        # check conner cases
        if self.sub_fields or self.sub_variants: 
            self.dtype.add(list if self.repeat else dict)
        if None in self.dtype:
            self.dtype.remove(None)
            self.dtype.add(type(None))
        # and make it compatible with `isinstance`
        self.dtype = tuple(self.dtype)

    def set_dtype(self, dtype: Union[None, type, Iterable[type]]):
        self.dtype = dtype
        self.reorg_dtype()

    def set_repeat(self, repeat: bool = True):
        self.repeat = repeat
        self.reorg_dtype

    def add_subfield(self, name: Union[str, "Argument"], 
                     *args, **kwargs) -> "Argument":
        if isinstance(name, Argument):
            newarg = name
        else:
            newarg = Argument(name, *args, **kwargs)
        self.sub_fields.append(newarg)
        self.reorg_dtype
        return newarg

    def add_subvariant(self, flag_name: Union[str, "Variant"], 
                       *args, **kwargs) -> "Variant":
        if isinstance(flag_name, Variant):
            newvrnt = flag_name
        else:
            newvrnt = Variant(flag_name, *args, **kwargs)
        self.sub_variants.append(newvrnt)
        self.reorg_dtype
        return newvrnt

    # above are creation part
    # below are type checking part

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

    # above are type checking part
    # below are doc generation part

    def gen_doc(self, parents: Optional[List[str]] = None, **kwargs) -> str:
        # the actual indentation is done here, and ONLY here
        doc_list = [
            self.gen_doc_head(parents, **kwargs),
            indent(self.gen_doc_path(parents, **kwargs), INDENT),
            indent(self.gen_doc_body(parents, **kwargs), INDENT)
        ]
        return "\n".join(filter(None, doc_list))

    def gen_doc_head(self, parents: Optional[List[str]] = None, **kwargs) -> str:
        typesig = "|".join([f"``{dt.__name__}``" for dt in self.dtype])
        if self.optional:
            typesig += ", optional"
        head = f"{self.name}: {typesig}"
        return head

    def gen_doc_path(self, parents: Optional[List[str]] = None, **kwargs) -> str:
        if parents is None:
            parents = []
        arg_path = [*parents, self.name]
        pathdoc = f"Argument path: {'/'.join(arg_path)}"
        return pathdoc

    def gen_doc_body(self, parents: Optional[List[str]] = None, **kwargs) -> str:
        if parents is None:
            parents = []
        arg_path = [*parents, self.name]
        body_list = []
        body_list.extend(wrap(self.doc))
        if self.repeat:
            body_list.append("This argument takes a list with "
                             "each element containing the following:")
        if self.sub_fields:
            # body_list.append("") # genetate a blank line
            # body_list.append("This argument accept the following sub arguments:")                
            for subarg in self.sub_fields:
                body_list.extend(["", subarg.gen_doc(arg_path, **kwargs)])
        if self.sub_variants:
            for subvrnt in self.sub_variants:
                body_list.extend(["", subvrnt.gen_doc(arg_path, **kwargs)])
        body = "\n".join(body_list)
        return body
        

class Variant:

    def __init__(self, 
            flag_name: str,
            choices: Optional[Iterable["Argument"]] = None,
            optional: bool = False,
            default_tag: str = "", # this is indeed necessary in case of optional
            doc: str = ""):
        self.flag_name = flag_name
        self.choice_dict = {}
        if choices is not None:
            self.extend_choices(choices)
        self.optional = optional
        if optional and not default_tag:
            raise ValueError("default_tag is needed if optional is set to be True")
        self.default_tag = default_tag
        self.doc = doc

    def __eq__(self, other: "Variant") -> bool:
        # do not compare doc 
        return (self.flag_name == other.flag_name 
            and self.choice_dict == other.choice_dict
            and self.optional == other.optional
            and self.default_tag == other.default_tag)

    def extend_choices(self, choices: Iterable["Argument"]):
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

    def set_optional(self, optional: bool = True, default_tag : str = ""):
        if optional and not default_tag:
            raise ValueError("default_tag is needed if optional is set to be True")
        self.optional = optional
        self.default_tag = default_tag

    def add_choice(self, tag: Union[str, "Argument"], 
                   *args, **kwargs) -> "Argument":
        if isinstance(tag, Argument):
            newarg = tag
        else:
            newarg = Argument(tag, *args, **kwargs)
        self.extend_choices([newarg])
        return newarg

    # above are creation part
    # below are type checking part

    def check(self, argdict: dict):
        choice = self._load_choice(argdict)
        # here we use check_value to flatten the tag
        choice.check_value(argdict)

    def _load_choice(self, argdict: dict) -> "Argument":
        if self.flag_name in argdict:
            tag = argdict[self.flag_name]
            return self.choice_dict[tag]
        elif self.optional:
            return self.choice_dict[self.default_tag]
        else:
            raise KeyError(f"Key `{self.flag_name}` is required "
                            "to choose variant but not found.")

    # above are type checking part
    # below are doc generation part
        
    def gen_doc(self, parents: Optional[List[str]] = None, **kwargs) -> str:
        body_list = []
        body_list.append(f"Depending on the value of *{self.flag_name}*, "
                          "different sub args are accepted. ") 
        body_list.extend(["", self.gen_doc_flag(parents, **kwargs)])
        for choice in self.choice_dict.values():
            body_list.extend([
                "", 
                f"When *{self.flag_name}* is set to ``{choice.name}``: ",
                choice.gen_doc_body(parents, **kwargs), 
            ])
        body = "\n".join(body_list)
        return body

    def gen_doc_flag(self, parents: Optional[List[str]] = None, **kwargs) -> str:
        headdoc = f"{self.flag_name}: ``str``"
        if self.optional:
            headdoc += f", default: {self.default_tag}"
        if parents is None:
            parents = []
        arg_path = [*parents, self.flag_name]
        pathdoc = indent(f"Argument path: {'/'.join(arg_path)}", INDENT)
        realdoc = indent(fill(self.doc), INDENT)
        return "\n".join(filter(None, [headdoc, pathdoc, realdoc]))