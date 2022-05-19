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


from typing import Union, Any, List, Dict, Iterable, Optional, Callable
from textwrap import indent
from copy import deepcopy
from enum import Enum
import fnmatch, re
import json


INDENT = "    " # doc is indented by four spaces
RAW_ANCHOR = False # whether to use raw html anchors or RST ones

# the third argument is the base path
HookArgKType = Callable[["Argument", dict, List[str]], None]
HookArgVType = Callable[["Argument", Any,  List[str]], None]
HookVrntType = Callable[["Variant",  dict, List[str]], None]
_DUMMYHOOK = lambda a,x,p: None # for doing nothing in traversing
class _Flags(Enum): NONE = 0 # for no value in dict (when optional)


class ArgumentError(Exception):
    """Base error class for invalid argument values in argchecking."""

    def __init__(self, 
                 path: Union[None, str, List[str]] = None, 
                 message: Optional[str] = None):
        super().__init__(message)
        if path is None:
            path = ""
        if not isinstance(path, str):
            path = "/".join(path)
        self.path = path.strip("/")
        self.message = message
    
    def __str__(self) -> str:
        loc_msg = ("at root location" if not self.path else
                  f"at location `{self.path}`")
        return f"[{loc_msg}] {self.message}"

class ArgumentKeyError(ArgumentError):
    """Error class for missing or invalid argument keys"""
    pass

class ArgumentTypeError(ArgumentError):
    """Error class for invalid argument data types"""
    pass

class ArgumentValueError(ArgumentError):
    """Error class for missing or invalid argument values"""
    pass


class Argument:
    """Define possible arguments and their types and properties.
    
    Each `Argument` instance contains a `name` and a `dtype`, that correspond
    to the key and value type of the actual argument. Additionally, it can
    include `sub_fields` and `sub_variants` to deal with nested dict arguments.

    Parameters
    ----------
    name : str
        The name of the current argument, i.e. the key in the arg dict.
    dtype : type or list of type
        The value type of the current argument, can be a list of possible types.
        `None` will be treated as `NoneType`
    sub_fields: list of Argument, optional
        If given, `dtype` is assumed to be dict, whose items correspond
        to the `Argument`s in the `sub_fields` list.
    sub_variants: list of Variants, optional
        If given, `dtype` is assumed to be dict, and its items are determined
        by the `Variant`s in the given list and the value of their flag keys.
    repeat: bool, optional
        If true,  `dtype` is assume to be list of dict and each dict consists
        of sub fields and sub variants described above. Defaults to false.
    optional: bool, optional
        If true, consider the current argument to be optional in checking.
    default: any value type
        The default value of the argument,used in normalization.
    alias: list of str
        Alternative names of the current argument, used in normalization.
    extra_check: callable
        Additional check to be done on the value of the argument.
        Should be a function that takes the value and returns whether it passes.
    doc: str
        The doc string of the argument, used in doc generation.
    fold_subdoc: bool, optional
        If true, no doc will be generated for sub args.

    Examples
    --------
    >>> ca = Argument("base", dict, [Argument("sub", int)])
    >>> ca.check({"base": {"sub1": 1}})
    >>> ca.check_value({"sub1": 1})

    for more detailed examples, please check the unit tests.
    """

    def __init__(self, 
            name: str,
            dtype: Union[None, type, Iterable[type]],
            sub_fields: Optional[Iterable["Argument"]] = None,
            sub_variants: Optional[Iterable["Variant"]] = None,
            repeat: bool = False,
            optional: bool = False,
            default: Any = _Flags.NONE,
            alias: Optional[Iterable[str]] = None,
            extra_check: Optional[Callable[[Any], bool]] = None,
            doc: str = "",
            fold_subdoc: bool = False):
        self.name = name
        self.dtype = dtype
        self.sub_fields : Dict[str, "Argument"] = {}
        self.sub_variants : Dict[str, "Variant"] = {}
        self.repeat = repeat
        self.optional = optional
        self.default = default
        self.alias = alias if alias is not None else []
        self.extra_check = extra_check
        self.doc = doc
        self.fold_subdoc = fold_subdoc
        # adding subfields and subvariants
        self.extend_subfields(sub_fields)
        self.extend_subvariants(sub_variants)
        # handle the format of dtype, makeit a tuple
        self._reorg_dtype()

    def __eq__(self, other: "Argument") -> bool:
        # do not compare doc and default
        # since they do not enter to the type checking
        fkey = lambda f: f.name
        vkey = lambda v: v.flag_name
        return (self.name         == other.name 
            and set(self.dtype)   == set(other.dtype)
            and self.sub_fields   == other.sub_fields
            and self.sub_variants == other.sub_variants
            and self.repeat       == other.repeat
            and self.optional     == other.optional)

    def __repr__(self) -> str:
        return f"<Argument {self.name}: {' | '.join(dd.__name__ for dd in self.dtype)}>"

    def __getitem__(self, key: str) -> "Argument":
        key = key.lstrip("/")
        if key in ("", "."):
            return self
        if key.startswith("["):
            vkey, rkey = key[1:].split("]", 1)
            if vkey.count("=") == 1:
                fkey, ckey = vkey.split("=")
            else:
                [fkey] = self.sub_variants.keys()
                ckey = vkey
            return self.sub_variants[fkey][ckey][rkey]
        p1, p2 = key.find("/"), key.find("[")
        if max(p1, p2) < 0: # not found
            return self.sub_fields[key]
        else: # at least one found
            p = p1 if p2 < 0 or  0 < p1 < p2 else p2
            skey, rkey = key[:p], key[p:]
            return self[skey][rkey]
    
    @property
    def I(self): 
        # return a dummy argument that only has self as a sub field
        # can be used in indexing
        return Argument("_", dict, [self])

    def _reorg_dtype(self):
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
        """Change the dtype of the current Argument."""
        self.dtype = dtype
        self._reorg_dtype()

    def set_repeat(self, repeat: bool = True):
        """Change the repeat attribute of the current Argument."""
        self.repeat = repeat
        self._reorg_dtype()
    
    def extend_subfields(self, sub_fields: Optional[Iterable["Argument"]]):
        """Add a list of sub fields to the current Argument."""
        if sub_fields is None:
            return
        assert all(isinstance(s, Argument) for s in sub_fields)
        update_nodup(self.sub_fields, ((s.name, s) for s in sub_fields),
            err_msg=f"building Argument `{self.name}`")
        self._reorg_dtype()

    def add_subfield(self, name: Union[str, "Argument"], 
                     *args, **kwargs) -> "Argument":
        """Add a sub field to the current Argument."""
        if isinstance(name, Argument):
            newarg = name
        else:
            newarg = Argument(name, *args, **kwargs)
        self.extend_subfields([newarg])
        return newarg

    def extend_subvariants(self, sub_variants: Optional[Iterable["Variant"]]):
        """Add a list of sub variants to the current Argument."""
        if sub_variants is None:
            return
        assert all(isinstance(s, Variant) for s in sub_variants)
        update_nodup(self.sub_variants, ((s.flag_name, s) for s in sub_variants),
            exclude=self.sub_fields.keys(),
            err_msg=f"building Argument `{self.name}`")
        self._reorg_dtype()

    def add_subvariant(self, flag_name: Union[str, "Variant"], 
                       *args, **kwargs) -> "Variant":
        """Add a sub variant to the current Argument."""
        if isinstance(flag_name, Variant):
            newvrnt = flag_name
        else:
            newvrnt = Variant(flag_name, *args, **kwargs)
        self.extend_subvariants([newvrnt])
        return newvrnt

    # above are creation part
    # below are general traverse part

    def flatten_sub(self, value: dict, path=None) -> Dict[str, "Argument"]:
        sub_dicts = [self.sub_fields]
        sub_dicts.extend(vrnt.flatten_sub(value, path) 
            for vrnt in self.sub_variants.values())
        flat_subs = {}
        update_nodup(flat_subs, *sub_dicts, 
            err_msg=f"flattening variants of {self.name}")
        return flat_subs

    def traverse(self, argdict: dict, 
                 key_hook: HookArgKType = _DUMMYHOOK,
                 value_hook: HookArgVType = _DUMMYHOOK,
                 sub_hook: HookArgKType = _DUMMYHOOK,
                 variant_hook: HookVrntType = _DUMMYHOOK, 
                 path: Optional[List[str]] = None):
        # first, do something with the key
        # then, take out the vaule and do something with it
        if path is None: path = []
        key_hook(self, argdict, path)
        if self.name in argdict:
            value = argdict[self.name]
            value_hook(self, value, path)
            newpath = [*path, self.name]
            # this is the key step that we traverse into the tree
            self.traverse_value(value, 
                key_hook, value_hook, sub_hook, variant_hook, newpath)

    def traverse_value(self, value: Any, 
                       key_hook: HookArgKType = _DUMMYHOOK,
                       value_hook: HookArgVType = _DUMMYHOOK,
                       sub_hook: HookArgKType = _DUMMYHOOK,
                       variant_hook: HookVrntType = _DUMMYHOOK,
                       path: Optional[List[str]] = None):
        # this is not private, and can be called directly
        # in the condition where there is no leading key
        if path is None: path = []
        if isinstance(value, dict):
            self._traverse_sub(value,
                key_hook, value_hook, sub_hook, variant_hook, path)
        if isinstance(value, list) and self.repeat:
            for idx, item in enumerate(value):
                self._traverse_sub(item,
                    key_hook, value_hook, sub_hook, variant_hook, [*path, str(idx)])

    def _traverse_sub(self, value: dict, 
                      key_hook: HookArgKType = _DUMMYHOOK,
                      value_hook: HookArgVType = _DUMMYHOOK,
                      sub_hook: HookArgKType = _DUMMYHOOK,
                      variant_hook: HookVrntType = _DUMMYHOOK,
                      path: Optional[List[str]] = None):
        assert isinstance(value, dict)
        if path is None: path = [self.name]
        sub_hook(self, value, path)
        for subvrnt in self.sub_variants.values():
            variant_hook(subvrnt, value, path)
        for subarg in self.flatten_sub(value, path).values():
            subarg.traverse(value, 
                key_hook, value_hook, sub_hook, variant_hook, path)

    # above are general traverse part
    # below are type checking part

    def check(self, argdict: dict, strict: bool = False):
        """Check whether `argdict` meets the structure defined in self.

        Will recursively check nested dicts according to 
        sub_fields and sub_variants. Raise an error if the check fails.
        
        Parameters
        ----------
        argdict: dict
            The arg dict to be checked
        strict: bool, optional
            If true, only keys defined in `Argument` are allowed.
        """
        if strict and len(argdict) != 1:
            raise ArgumentKeyError(None,
                "only one single key of arg name is allowed "
                "for check in strict mode at top level, "
                "use check_value if you are checking subfields")
        self.traverse(argdict, 
            key_hook=Argument._check_exist,
            value_hook=Argument._check_data,
            sub_hook=Argument._check_strict if strict else _DUMMYHOOK)

    def check_value(self, value: Any, strict: bool = False):
        """Check the value without the leading key.

        Same as `check({self.name: value})`. 
        Raise an error if the check fails.
        
        Parameters
        ----------
        value: any value type
            The value to be checked
        strict: bool, optional
            If true, only keys defined in `Argument` are allowed.
        """
        self.traverse_value(value, 
            key_hook=Argument._check_exist,
            value_hook=Argument._check_data,
            sub_hook=Argument._check_strict if strict else _DUMMYHOOK)

    def _check_exist(self, argdict: dict, path=None):
        if self.optional is True:
            return
        if self.name not in argdict:
            raise ArgumentKeyError(path,
                f"key `{self.name}` is required "
                 "in arguments but not found")

    def _check_data(self, value: Any, path=None):
        if not isinstance(value, self.dtype):
            raise ArgumentTypeError(path,
                f"key `{self.name}` gets wrong value type, "
                f"requires <{'|'.join(dd.__name__ for dd in self.dtype)}> "
                f"but gets <{type(value).__name__}>")
        if self.extra_check is not None and not self.extra_check(value):
            raise ArgumentValueError(path,
                f"key `{self.name}` gets bad value "
                "that fails to pass its extra checking")

    def _check_strict(self, value: dict, path=None):
        allowed_keys = self.flatten_sub(value, path).keys()
        # curpath = [*path, self.name]
        if not len(allowed_keys):
            # no allowed keys defined, allow any keys
            return
        for name in value.keys():
            if name not in allowed_keys:
                raise ArgumentKeyError(path,
                    f"undefined key `{name}` is "
                     "not allowed in strict mode")

    # above are type checking part
    # below are normalizing part

    def normalize(self, argdict: dict, inplace: bool = False, 
                  do_default: bool = True, do_alias: bool = True, 
                  trim_pattern: Optional[str] = None):
        """Modify `argdict` so that it meets the Argument structure
        
        Normalization can add default values to optional args, 
        substitute alias by its standard names, and discard unnecessary
        args following given pattern.

        Parameters
        ----------
        argdict: dict
            The arg dict to be normalized.
        inplace: bool, optional
            If true, modify the given dict. Otherwise return a new one.
        do_default: bool, optional
            Whether to add default values.
        do_alias: bool, optional
            Whether to transform alias names.
        trim_pattern: str, optional
            If given, discard keys that matches the glob pattern.

        Returns
        -------
        dict:
            The normalized arg dict.
        """
        if not inplace:
            argdict = deepcopy(argdict)
        if do_alias:
            self.traverse(argdict, 
                key_hook=Argument._convert_alias,
                variant_hook=Variant._convert_choice_alias)
        if do_default:
            self.traverse(argdict, 
                key_hook=Argument._assign_default)
        if trim_pattern is not None:
            trim_by_pattern(argdict, trim_pattern, reserved=[self.name])
            self.traverse(argdict, sub_hook=lambda a, d, p: 
                trim_by_pattern(d, trim_pattern, a.flatten_sub(d, p).keys()))
        return argdict

    def normalize_value(self, value: Any, inplace: bool = False, 
                        do_default: bool = True, do_alias: bool = True, 
                        trim_pattern: Optional[str] = None):
        """Modify the value so that it meets the Argument structure
        
        Same as `normalize({self.name: value})[self.name]`.

        Parameters
        ----------
        value: any value type
            The arg value to be normalized.
        inplace: bool, optional
            If true, modify the given dict. Otherwise return a new one.
        do_default: bool, optional
            Whether to add default values.
        do_alias: bool, optional
            Whether to transform alias names.
        trim_pattern: str, optional
            If given, discard keys that matches the glob pattern.

        Returns
        -------
        value:
            The normalized arg value.
        """
        if not inplace:
            value = deepcopy(value)
        if do_alias:
            self.traverse_value(value, 
                key_hook=Argument._convert_alias,
                variant_hook=Variant._convert_choice_alias)
        if do_default:
            self.traverse_value(value, 
                key_hook=Argument._assign_default)
        if trim_pattern is not None:
            self.traverse_value(value, sub_hook=lambda a, d, p: 
                trim_by_pattern(d, trim_pattern, a.flatten_sub(d, p).keys()))
        return value

    def _assign_default(self, argdict: dict, path=None):
        if (self.name not in argdict 
        and self.optional 
        and self.default is not _Flags.NONE):
            argdict[self.name] = self.default

    def _convert_alias(self, argdict: dict, path=None):
        if self.name not in argdict:
            for alias in self.alias:
                if alias in argdict:
                    argdict[self.name] = argdict.pop(alias)
                    return

    # above are normalizing part
    # below are doc generation part

    def gen_doc(self, path: Optional[List[str]] = None, **kwargs) -> str:
        """Generate doc string for the current Argument."""
        # the actual indentation is done here, and ONLY here
        if path is None:
            path = []
        sub_paths = [*path, self.name]
        doc_list = [
            self.gen_doc_head(sub_paths, **kwargs),
            indent(self.gen_doc_path(sub_paths, **kwargs), INDENT),
            indent(self.gen_doc_body(sub_paths, **kwargs), INDENT)
        ]
        return "\n".join(filter(None, doc_list))

    def gen_doc_head(self, path: Optional[List[str]] = None, **kwargs) -> str:
        typesig = "| type: " + " | ".join([f"``{dt.__name__}``" for dt in self.dtype])
        if self.optional:
            typesig += ", optional"
            if self.default is not _Flags.NONE:
                typesig += f", default: ``{self.default}``"
        if self.alias:
            typesig += f", alias{'es' if len(self.alias) > 1 else ''}: "
            typesig += ', '.join(f"*{al}*" for al in self.alias)
        head = f"{self.name}: \n{indent(typesig, INDENT)}"
        if kwargs.get("make_anchor"):
            head = f"{make_rst_refid(path)}\n" + head
        return head

    def gen_doc_path(self, path: Optional[List[str]] = None, **kwargs) -> str:
        if path is None:
            path = [self.name]
        pathdoc = f"| argument path: ``{'/'.join(path)}``\n"
        return pathdoc

    def gen_doc_body(self, path: Optional[List[str]] = None, **kwargs) -> str:
        body_list = []
        if self.doc:
            body_list.append(self.doc + "\n")
        if not self.fold_subdoc:
            if self.repeat:
                body_list.append("This argument takes a list with "
                                "each element containing the following: \n")
            if self.sub_fields:
                # body_list.append("") # genetate a blank line
                # body_list.append("This argument accept the following sub arguments:")                
                for subarg in self.sub_fields.values():
                    body_list.append(subarg.gen_doc(path, **kwargs))
            if self.sub_variants:
                showflag = len(self.sub_variants) > 1
                for subvrnt in self.sub_variants.values():
                    body_list.append(subvrnt.gen_doc(path, showflag, **kwargs))
        body = "\n".join(body_list)
        return body


class Variant:
    """Define multiple choices of possible argument sets.
    
    Each Variant contains a `flag_name` and a list of choices 
    that are represented by `Argument`s. The choice is picked if its name 
    matches the value of `flag_name` in the actual arguments. The actual 
    arguments should then be a dict containing `flag_name` and sub fields
    of the picked choice.

    Parameters
    ----------
    flag_name: str
        The name of the key to be used as the switching flag.
    choices: list of Argument
        A list of possible choices. Each of them should be an `Argument`.
        The name of the `Argument` serves as the tag in the switching flag.
    optional: bool, optional
        If true, the flag_name can be optional and defaults to `defalut_flag`.
    default_tag: str, optional
        Needed if optional is true.
    doc: str, optional
        The doc string used in document generation.

    Notes
    -----
    This class should only be used in sub variants of the `Argument` class.
    """

    def __init__(self, 
            flag_name: str,
            choices: Optional[Iterable["Argument"]] = None,
            optional: bool = False,
            default_tag: str = "", # this is indeed necessary in case of optional
            doc: str = ""):
        self.flag_name = flag_name
        self.choice_dict : Dict[str, Argument] = {}
        self.choice_alias : Dict[str, str] = {}
        self.extend_choices(choices)
        self.optional = optional
        if optional and not default_tag:
            raise ValueError("default_tag is needed if optional is set to be True")
        self.set_default(default_tag)
        self.doc = doc

    def __eq__(self, other: "Variant") -> bool:
        # do not compare doc 
        return (self.flag_name == other.flag_name 
            and self.choice_dict == other.choice_dict
            and self.optional == other.optional
            and self.default_tag == other.default_tag)
    
    def __repr__(self) -> str:
        return f"<Variant {self.flag_name} in {{ {', '.join(self.choice_dict.keys())} }}>"

    def __getitem__(self, key: str) -> "Argument":
        return self.choice_dict[key]

    def set_default(self, default_tag : Union[bool, str]):
        """Change the default tag of the current Variant."""
        if not default_tag:
            self.optional = False
            self.default_tag = ""
        else:
            if default_tag not in self.choice_dict:
                raise ValueError(f"trying to set invalid default_tag `{default_tag}`")
            self.optional = True
            self.default_tag = default_tag

    def extend_choices(self, choices: Optional[Iterable["Argument"]]):
        """Add a list of choice Arguments to the current Variant"""
        # choices is a list of arguments 
        # whose name is treated as the switch tag
        # we convert it into a dict for better reference
        # and avoid duplicate tags
        if choices is None:
            return
        update_nodup(self.choice_dict, ((c.name, c) for c in choices),
            exclude={self.flag_name},
            err_msg=f"Variant with flag `{self.flag_name}`")
        update_nodup(self.choice_alias, 
            *[[(a, c.name) for a in c.alias] for c in choices],
            exclude={self.flag_name, *self.choice_dict.keys()},
            err_msg=f"building alias dict for Variant with flag `{self.flag_name}`")

    def add_choice(self, tag: Union[str, "Argument"], 
                   _dtype: Union[None, type, Iterable[type]] = dict,
                   *args, **kwargs) -> "Argument":
        """Add a choice Argument to the current Variant"""
        if isinstance(tag, Argument):
            newarg = tag
        else:
            newarg = Argument(tag, _dtype, *args, **kwargs)
        self.extend_choices([newarg])
        return newarg
    
    def dummy_argument(self):
        return Argument(name=self.flag_name, dtype=str, 
                        optional=self.optional, default=self.default_tag,
                        sub_fields=None, sub_variants=None, repeat=False,
                        alias=None, extra_check=None, 
                        doc=f"dummy Argument converted from Variant {self.flag_name}")

    # above are creation part
    # below are helpers for traversing

    def get_choice(self, argdict: dict, path=None) -> "Argument":
        if self.flag_name in argdict:
            tag = argdict[self.flag_name]
            if tag in self.choice_dict:
                return self.choice_dict[tag]
            elif tag in self.choice_alias:
                return self.choice_dict[self.choice_alias[tag]]
            else:
                raise ArgumentValueError(path,
                    f"get invalid choice `{tag}` for flag key `{self.flag_name}`.")
        elif self.optional:
            return self.choice_dict[self.default_tag]
        else:
            raise ArgumentKeyError(path,
                f"key `{self.flag_name}` is required "
                 "to choose variant but not found.")

    def flatten_sub(self, argdict: dict, path=None) -> Dict[str, "Argument"]:
        choice = self.get_choice(argdict, path)
        fields = {self.flag_name: self.dummy_argument(), # as a placeholder
                  **choice.flatten_sub(argdict, path)}
        return fields

    def _convert_choice_alias(self, argdict: dict, path=None):
        if self.flag_name in argdict:
            tag = argdict[self.flag_name]
            if tag not in self.choice_dict and tag in self.choice_alias:
                argdict[self.flag_name] = self.choice_alias[tag]

    # above are traversing part
    # below are doc generation part

    def gen_doc(self, path: Optional[List[str]] = None, 
                      showflag : bool = False, **kwargs) -> str:
        body_list = [""]
        body_list.append(f"Depending on the value of *{self.flag_name}*, "
                          "different sub args are accepted. \n") 
        body_list.append(self.gen_doc_flag(path, showflag=showflag, **kwargs))
        fnstr = f"*{self.flag_name}*"
        if kwargs.get("make_link"):
            if not kwargs.get("make_anchor"):
                raise ValueError("`make_link` only works with `make_anchor` set")
            fnstr, target = make_ref_pair(path+[self.flag_name], fnstr, "flag")
            body_list.append(target + "\n")
        for choice in self.choice_dict.values():
            body_list.append("")
            choice_path = self._make_cpath(choice.name, path, showflag)
            if kwargs.get("make_anchor"):
                body_list.append(make_rst_refid(choice_path))
            c_alias = (f" (or its alias{'es' if len(choice.alias) > 1 else ''} "
                      + ", ".join(f"``{al}``" for al in choice.alias) + ")"
                      if choice.alias else "")
            body_list.extend([
                f"When {fnstr} is set to ``{choice.name}``{c_alias}: \n",
                choice.gen_doc_body(choice_path, **kwargs), 
            ])
        body = "\n".join(body_list)
        return body

    def gen_doc_flag(self, path: Optional[List[str]] = None, **kwargs) -> str:
        headdoc = f"{self.flag_name}:"
        typedoc = "| type: ``str`` (flag key)"
        if self.optional:
            typedoc += f", default: ``{self.default_tag}``"
        typedoc = indent(typedoc, INDENT)
        if path is None:
            path = []
        arg_path = [*path, self.flag_name]
        pathdoc = indent(f"| argument path: ``{'/'.join(arg_path)}`` ", INDENT)
        if kwargs.get("make_link"):
            if not kwargs.get("make_anchor"):
                raise ValueError("`make_link` only works with `make_anchor` being set")
            l_choice, l_target = zip(*(make_ref_pair(
                    self._make_cpath(c.name, path, kwargs["showflag"]),
                    text=f"``{c.name}``", prefix="code") 
                for c in self.choice_dict.values()))
            targetdoc = indent('\n'.join(l_target) + "\n", INDENT)
        else:
            l_choice = [c.name for c in self.choice_dict.values()]
            targetdoc = None
        choicedoc = indent("| possible choices: " + ", ".join(l_choice), INDENT)
        realdoc = indent(self.doc + "\n", INDENT) if self.doc else None
        anchor = make_rst_refid(arg_path) if kwargs.get("make_anchor") else None
        allparts = [anchor, headdoc, typedoc, pathdoc, choicedoc, "", realdoc, targetdoc]
        return "\n".join(filter(None.__ne__, allparts))

    def _make_cpath(self, cname: str, 
                    path: Optional[List[str]] = None, 
                    showflag : bool = False):
        f_str = f"{self.flag_name}=" if showflag else ""
        c_str = f"[{f_str}{cname}]"
        cpath = [*path[:-1], path[-1]+c_str] if path else [c_str]
        return cpath


def make_rst_refid(name):
    if not isinstance(name, str):
        name = '/'.join(name)
    return (f'.. _`{name}`: \n' if not RAW_ANCHOR
            else f'.. raw:: html\n\n   <a id="{name}"></a>')


def make_ref_pair(path, text=None, prefix=None):
    if not isinstance(path, str):
        path = '/'.join(path)
    tgt = f"`{path}`_" if not RAW_ANCHOR else f"#{path}"
    ref = ("" if not prefix else f"{prefix}:") + path
    inline = f'`{ref}`_' if not text else f'|{ref}|_'
    target = f'.. _`{ref}`: {tgt}'
    if text:
        target = f'.. |{ref}| replace:: {text}\n' + target
    return inline, target


def update_nodup(this : dict, 
                 *others : Union[dict, Iterable[tuple]], 
                 exclude : Optional[Iterable] = None,
                 err_msg : Optional[str] = None):
    for pair in others:
        if isinstance(pair, dict):
            pair = pair.items()
        for k, v in pair:
            if k in this or (exclude and k in exclude):
                raise ValueError(f"duplicate key `{k}` when updating dict"
                                 +("" if err_msg is None else f"in {err_msg}"))
            this[k] = v
    return this


def trim_by_pattern(argdict: dict, pattern: str, 
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


class ArgumentEncoder(json.JSONEncoder):
    """Extended JSON Encoder to encode Argument object:

    Examples
    --------
    >>> json.dumps(some_arg, cls=ArgumentEncoder)
    """
    def default(self, obj) -> Dict[str, Union[str, bool, List]]:
        """Generate a dict containing argument information, making it ready to be encoded
        to JSON string.

        Notes
        -----
        All object in the dict should be JSON serializable.

        Returns
        -------
        dict: Dict
            a dict containing argument information
        """
        if isinstance(obj, Argument):
            output = {
                "object": "Argument",
                "name": obj.name,
                "type": obj.dtype,
                "optional": obj.optional,
                "alias": obj.alias,
                "doc": obj.doc,
                "repeat": obj.repeat,
                "sub_fields": obj.sub_fields,
                "sub_variants": obj.sub_variants,
            }
            if obj.optional and obj.default is not _Flags.NONE:
                output['default'] = obj.default
            return output
        elif isinstance(obj, Variant):
            return {
                "object": "Variant",
                "flag_name": obj.flag_name,
                "optional": obj.optional,
                "default_tag": obj.default_tag,
                "choice_dict": obj.choice_dict,
                "choice_alias": obj.choice_alias,
                "doc": obj.doc,
            }
        elif isinstance(obj, type):
            return obj.__name__
        return json.JSONEncoder.default(self, obj)
