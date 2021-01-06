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


from typing import Union, Any, List, Iterable, Optional, Callable
from textwrap import wrap, fill, indent
from copy import deepcopy
from enum import Enum
import fnmatch, re


INDENT = "    " # doc is indented by four spaces
DUMMYHOOK = lambda a,x: None
class _Flags(Enum): NONE = 0 # for no value in dict

class Argument:

    def __init__(self, 
            name: str,
            dtype: Union[None, type, Iterable[type]],
            sub_fields: Optional[Iterable["Argument"]] = None,
            sub_variants: Optional[Iterable["Variant"]] = None,
            repeat: bool = False,
            optional: bool = False,
            default: Any = _Flags.NONE,
            alias: Optional[Iterable[str]] = None,
            doc: str = ""):
        self.name = name
        self.dtype = dtype
        self.sub_fields = sub_fields if sub_fields is not None else []
        self.sub_variants = sub_variants if sub_variants is not None else []
        self.repeat = repeat
        self.optional = optional
        self.default = default
        self.alias = alias if alias is not None else []
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
            and sorted(self.sub_variants, key=vkey) == sorted(other.sub_variants, key=vkey)
            and self.repeat == other.repeat
            and self.optional == other.optional)

    def reorg_dtype(self):
        if isinstance(self.dtype, type) or self.dtype is None:
            self.dtype = [self.dtype]
        # remove duplicate
        self.dtype = {dt if type(dt) is type else type(dt) for dt in self.dtype}
        # check conner cases
        if self.sub_fields or self.sub_variants: 
            self.dtype.add(list if self.repeat else dict)
        if self.optional and self.default is not _Flags.NONE:
            self.dtype.add(type(self.default))
        # and make it compatible with `isinstance`
        self.dtype = tuple(self.dtype)

    def set_dtype(self, dtype: Union[None, type, Iterable[type]]):
        self.dtype = dtype
        self.reorg_dtype()

    def set_repeat(self, repeat: bool = True):
        self.repeat = repeat
        self.reorg_dtype()

    def add_subfield(self, name: Union[str, "Argument"], 
                     *args, **kwargs) -> "Argument":
        if isinstance(name, Argument):
            newarg = name
        else:
            newarg = Argument(name, *args, **kwargs)
        self.sub_fields.append(newarg)
        self.reorg_dtype()
        return newarg

    def add_subvariant(self, flag_name: Union[str, "Variant"], 
                       *args, **kwargs) -> "Variant":
        if isinstance(flag_name, Variant):
            newvrnt = flag_name
        else:
            newvrnt = Variant(flag_name, *args, **kwargs)
        self.sub_variants.append(newvrnt)
        self.reorg_dtype()
        return newvrnt

    # above are creation part
    # below are general traverse part

    def traverse(self, argdict: dict, 
                 key_hook: Callable[["Argument", dict], None] = DUMMYHOOK,
                 value_hook: Callable[["Argument", Any], None] = DUMMYHOOK,
                 sub_hook: Callable[["Argument", dict], None] = DUMMYHOOK,
                 variant_hook: Callable[["Variant", dict], None] = DUMMYHOOK):
        # first, do something with the key
        # then, take out the vaule and do something with it
        key_hook(self, argdict)
        if self.name in argdict:
            # this is the key step that we traverse into the tree
            self.traverse_value(argdict[self.name], 
                key_hook, value_hook, sub_hook, variant_hook)

    def traverse_value(self, value: Any, 
                       key_hook: Callable[["Argument", dict], None] = DUMMYHOOK,
                       value_hook: Callable[["Argument", Any], None] = DUMMYHOOK,
                       sub_hook: Callable[["Argument", dict], None] = DUMMYHOOK,
                       variant_hook: Callable[["Variant", dict], None] = DUMMYHOOK):
        # this is not private, and can be called directly
        # in the condition where there is no leading key
        value_hook(self, value)
        if isinstance(value, dict):
            sub_hook(self, value)
            self._traverse_subfield(value, 
                key_hook, value_hook, sub_hook, variant_hook)
            self._traverse_subvariant(value, 
                key_hook, value_hook, sub_hook, variant_hook)
        if isinstance(value, list) and self.repeat:
            for item in value:
                sub_hook(self, item)
                self._traverse_subfield(item, 
                    key_hook, value_hook, sub_hook, variant_hook)
                self._traverse_subvariant(item, 
                    key_hook, value_hook, sub_hook, variant_hook)
    
    def _traverse_subfield(self, value: dict, *args, **kwargs):
        assert isinstance(value, dict)
        for subarg in self.sub_fields:
            subarg.traverse(value, *args, **kwargs)

    def _traverse_subvariant(self, value: dict, *args, **kwargs):
        assert isinstance(value, dict)
        for subvrnt in self.sub_variants:
            subvrnt.traverse(value, *args, **kwargs)

    # above are general traverse part
    # below are type checking part

    def check(self, argdict: dict, strict: bool = False):
        if strict and len(argdict) != 1:
            raise KeyError("only one single key of arg name is allowed "
                           "for check in strict mode at top level, "
                           "use check_value if you are checking subfields")
        self.traverse(argdict, 
            key_hook=Argument._check_exist,
            value_hook=Argument._check_dtype,
            sub_hook=Argument._check_strict if strict else DUMMYHOOK)

    def check_value(self, argdict: dict, strict: bool = False):
        self.traverse_value(argdict, 
            key_hook=Argument._check_exist,
            value_hook=Argument._check_dtype,
            sub_hook=Argument._check_strict if strict else DUMMYHOOK)
            
    def _check_exist(self, argdict: dict):
        if self.optional is True:
            return
        if self.name not in argdict:
            raise KeyError(f"key `{self.name}` is required "
                            "in arguments but not found")

    def _check_dtype(self, value: Any):
        if not isinstance(value, self.dtype):
            raise TypeError(f"key `{self.name}` gets wrong value type: "
                            f"requires {self.dtype} but gets {type(value)}")

    def _check_strict(self, value: dict):
        allowed = self._get_allowed_sub(value)
        allowed_set = set(allowed)
        assert len(allowed) == len(allowed_set), "duplicated keys!"
        for name in value.keys():
            if name not in allowed_set:
                raise KeyError(f"undefined key `{name}` is "
                                "not allowed in strict mode")
        
    def _get_allowed_sub(self, value: dict) -> List[str]:
        allowed = [subarg.name for subarg in self.sub_fields]
        for subvrnt in self.sub_variants:
            allowed.extend(subvrnt._get_allowed_sub(value))
        return allowed

    # above are type checking part
    # below are normalizing part

    def normalize(self, argdict: dict, inplace: bool = False, 
                  do_default: bool = True, do_alias: bool = True, 
                  trim_pattern: Optional[str] = None):
        if not inplace:
            argdict = deepcopy(argdict)
        if do_alias:
            self.traverse(argdict, 
                key_hook=Argument._convert_alias,
                variant_hook=Variant._convert_alias)
        if do_default:
            self.traverse(argdict, 
                key_hook=Argument._assign_default,
                variant_hook=Variant._assign_default)
        if trim_pattern is not None:
            self._trim_unrequired(argdict, trim_pattern, reserved=[self.name])
            self.traverse(argdict, sub_hook=lambda a, d: 
                Argument._trim_unrequired(d, trim_pattern, a._get_allowed_sub(d)))
        return argdict

    def normalize_value(self, value: Any, inplace: bool = False, 
                        do_default: bool = True, do_alias: bool = True, 
                        trim_pattern: Optional[str] = None):
        if not inplace:
            value = deepcopy(value)
        if do_alias:
            self.traverse_value(value, 
                key_hook=Argument._convert_alias,
                variant_hook=Variant._convert_alias)
        if do_default:
            self.traverse_value(value, 
                key_hook=Argument._assign_default,
                variant_hook=Variant._assign_default)
        if trim_pattern is not None:
            self.traverse_value(value, sub_hook=lambda a, d: 
                Argument._trim_unrequired(d, trim_pattern, a._get_allowed_sub(d)))
        return value

    def _assign_default(self, argdict: dict):
        if (self.name not in argdict 
        and self.optional 
        and self.default is not _Flags.NONE):
            argdict[self.name] = self.default

    def _convert_alias(self, argdict: dict):
        if self.name not in argdict:
            for alias in self.alias:
                if alias in argdict:
                    argdict[self.name] = argdict.pop(alias)
                    return

    @staticmethod
    def _trim_unrequired(argdict: dict, pattern: str, 
                         reserved: Optional[List[str]] = None,
                         use_regex: bool = False):
        rep = fnmatch.translate(pattern) if not use_regex else pattern
        rem = re.compile(rep)
        if reserved:
            conflict = list(filter(rem.match, reserved))
            if conflict:
                raise ValueError(f"pattern `{pattern}` conflicts with the "
                                 f"following reserved names: {', '.join(conflict)}")
        unrequired = list(filter(rem.match, argdict.keys()))
        for key in unrequired:
            argdict.pop(key)

    # above are normalizing part
    # below are doc generation part

    def gen_doc(self, paths: Optional[List[str]] = None, **kwargs) -> str:
        # the actual indentation is done here, and ONLY here
        if paths is None:
            paths = []
        sub_paths = [*paths, self.name]
        doc_list = [
            self.gen_doc_head(sub_paths, **kwargs),
            indent(self.gen_doc_path(sub_paths, **kwargs), INDENT),
            indent(self.gen_doc_body(sub_paths, **kwargs), INDENT)
        ]
        return "\n".join(filter(None, doc_list))

    def gen_doc_head(self, paths: Optional[List[str]] = None, **kwargs) -> str:
        typesig = "| type: " + " | ".join([f"``{dt.__name__}``" for dt in self.dtype])
        if self.optional:
            typesig += ", optional"
            if self.default is not _Flags.NONE:
                typesig += f", default: ``{self.default}``"
        head = f"{self.name}: \n{indent(typesig, INDENT)}"
        if kwargs.get("make_anchor"):
            head = f"{make_rst_refid(paths)}\n" + head
        return head

    def gen_doc_path(self, paths: Optional[List[str]] = None, **kwargs) -> str:
        if paths is None:
            paths = [self.name]
        pathdoc = f"| argument path: ``{'/'.join(paths)}``\n"
        return pathdoc

    def gen_doc_body(self, paths: Optional[List[str]] = None, **kwargs) -> str:
        body_list = []
        if self.doc:
            body_list.append(self.doc + "\n")
        if self.repeat:
            body_list.append("This argument takes a list with "
                             "each element containing the following: \n")
        if self.sub_fields:
            # body_list.append("") # genetate a blank line
            # body_list.append("This argument accept the following sub arguments:")                
            for subarg in self.sub_fields:
                body_list.append(subarg.gen_doc(paths, **kwargs))
        if self.sub_variants:
            for subvrnt in self.sub_variants:
                body_list.append(subvrnt.gen_doc(paths, **kwargs))
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
        self.alias_dict = {}
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
            # also update alias here
            for atag in arg.alias:
                if atag in self.choice_dict or atag in self.alias_dict:
                    raise ValueError(f"duplicate alias tag `{atag}` appears in "
                                     f"variant with flag `{self.flag_name}` "
                                     f"and choice name `{arg.name}`")
                self.alias_dict[atag] = arg.name

    def set_default(self, default_tag : Union[bool, str]):
        if not default_tag:
            self.optional = False
            self.default_tag = ""
        else:
            assert default_tag in self.choice_dict
            self.optional = True
            self.default_tag = default_tag

    def add_choice(self, tag: Union[str, "Argument"], 
                   dtype: Union[None, type, Iterable[type]] = dict,
                   *args, **kwargs) -> "Argument":
        if isinstance(tag, Argument):
            newarg = tag
        else:
            newarg = Argument(tag, dtype, *args, **kwargs)
        self.extend_choices([newarg])
        return newarg

    # above are creation part
    # below are general traverse part

    def traverse(self, argdict: dict, 
                 key_hook: Callable[["Argument", dict], None] = DUMMYHOOK,
                 value_hook: Callable[["Argument", Any], None] = DUMMYHOOK,
                 sub_hook: Callable[["Argument", dict], None] = DUMMYHOOK,
                 variant_hook: Callable[["Variant", dict], None] = DUMMYHOOK):
        variant_hook(self, argdict)
        choice = self._load_choice(argdict)
        # here we use check_value to flatten the tag
        choice.traverse_value(argdict,
            key_hook, value_hook, sub_hook, variant_hook)

    def _load_choice(self, argdict: dict) -> "Argument":
        if self.flag_name in argdict:
            tag = argdict[self.flag_name]
            return self.choice_dict[tag]
        elif self.optional:
            return self.choice_dict[self.default_tag]
        else:
            raise KeyError(f"key `{self.flag_name}` is required "
                            "to choose variant but not found.")

    def _get_allowed_sub(self, argdict: dict) -> List[str]:
        allowed = [self.flag_name]
        choice = self._load_choice(argdict)
        allowed.extend(choice._get_allowed_sub(argdict))
        return allowed

    def _assign_default(self, argdict: dict):
        if self.flag_name not in argdict and self.optional:
            argdict[self.flag_name] = self.default_tag

    def _convert_alias(self, argdict: dict):
        if self.flag_name in argdict:
            tag = argdict[self.flag_name]
            if tag not in self.choice_dict and tag in self.alias_dict:
                argdict[self.flag_name] = self.alias_dict[tag]

    # above are type checking part
    # below are doc generation part
        
    def gen_doc(self, paths: Optional[List[str]] = None, **kwargs) -> str:
        body_list = [""]
        body_list.append(f"Depending on the value of *{self.flag_name}*, "
                          "different sub args are accepted. \n") 
        body_list.append(self.gen_doc_flag(paths, **kwargs))
        for choice in self.choice_dict.values():
            c_str = f"[{choice.name}]"
            choice_path = [*paths[:-1], paths[-1]+c_str] if paths else [c_str]
            body_list.append("")
            if kwargs.get("make_anchor"):
                body_list.append(make_rst_refid(choice_path))
            body_list.extend([
                f"When *{self.flag_name}* is set to ``{choice.name}``: \n",
                choice.gen_doc_body(choice_path, **kwargs), 
            ])
        body = "\n".join(body_list)
        return body

    def gen_doc_flag(self, paths: Optional[List[str]] = None, **kwargs) -> str:
        headdoc = f"{self.flag_name}:"
        typedoc = "| type: ``str`` (flag key)"
        if self.optional:
            typedoc += f", default: ``{self.default_tag}``"
        typedoc = indent(typedoc, INDENT)
        if paths is None:
            paths = []
        arg_path = [*paths, self.flag_name]
        pathdoc = indent(f"| argument path: ``{'/'.join(arg_path)}`` \n", INDENT)
        realdoc = indent(self.doc + "\n", INDENT) if self.doc else None
        anchor = make_rst_refid(arg_path) if kwargs.get("make_anchor") else None
        allparts = [anchor, headdoc, typedoc, pathdoc, realdoc]
        return "\n".join(filter(None, allparts))


def make_rst_refid(name):
    if not isinstance(name, str):
        name = '/'.join(name)
    return f'.. raw:: html\n\n   <a id="{name}"></a>'
