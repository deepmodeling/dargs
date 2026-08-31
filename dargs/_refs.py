"""Loading and resolving external ``$ref`` mappings."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._context import TraversalContext

__all__ = ["load_ref", "resolve_ref"]


def load_ref(ref_path: str) -> dict:
    """Load a mapping from a JSON or YAML file referenced by ``$ref``.

    Parameters
    ----------
    ref_path : str
        Path to the external file. Supported extensions are ``.json``,
        ``.yml``, and ``.yaml``.

    Returns
    -------
    dict
        The loaded mapping.

    Raises
    ------
    ValueError
        If the extension is unsupported or the file does not contain a
        top-level mapping.
    ImportError
        If a YAML file is requested without PyYAML installed.
    """
    ext = os.path.splitext(ref_path)[1].lower()
    if ext == ".json":
        with open(ref_path, encoding="utf-8") as f:
            loaded = json.load(f)
    elif ext in (".yml", ".yaml"):
        try:
            import yaml
        except ImportError as e:
            raise ImportError(
                "pyyaml is required to load YAML files referenced by $ref. "
                "Install it with: pip install pyyaml"
            ) from e
        with open(ref_path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
    else:
        raise ValueError(
            f"Unsupported file extension `{ext}` for $ref. "
            "Supported extensions are: .json, .yml, .yaml"
        )
    if not isinstance(loaded, dict):
        raise ValueError(
            f"Referenced file {ref_path!r} must contain a mapping/object at the top "
            f"level, but got {type(loaded).__name__!r}."
        )
    return loaded


def resolve_ref(d: dict, context: TraversalContext) -> TraversalContext:
    """Resolve ``$ref`` entries and return the child traversal context.

    Relative references are resolved from the file that supplied the current
    mapping. ``context.ref_chain`` tracks active ancestor files so cycles that
    cross nested mappings are detected without treating sibling references as
    cyclic.

    The mapping is modified in place, matching the historical private
    ``dargs.dargs._resolve_ref`` helper.

    Returns
    -------
    TraversalContext
        Context updated with the directory and active reference chain for
        descendants.

    Raises
    ------
    ValueError
        If references are disabled or a cyclic reference is detected.
    """
    base_dir = context.ref_base_dir if context.ref_base_dir is not None else os.curdir
    if "$ref" not in d:
        return context.with_ref_state(
            ref_base_dir=base_dir,
            ref_chain=context.ref_chain,
        )
    if not context.allow_ref:
        raise ValueError(
            "$ref is not allowed by default. "
            "Pass allow_ref=True to enable loading from external files."
        )

    ref_chain = context.ref_chain
    while "$ref" in d:
        ref_path = d.pop("$ref")
        resolved_ref_path = (
            ref_path if os.path.isabs(ref_path) else os.path.join(base_dir, ref_path)
        )
        canonical_ref_path = os.path.realpath(resolved_ref_path)
        if canonical_ref_path in ref_chain:
            raise ValueError(f"Cyclic $ref detected for path: {canonical_ref_path!r}")
        ref_chain = (*ref_chain, canonical_ref_path)
        loaded = load_ref(canonical_ref_path)
        # A chained relative reference belongs to the file that declares it.
        base_dir = os.path.dirname(canonical_ref_path)
        merged = {**loaded, **d}
        d.clear()
        d.update(merged)

    return context.with_ref_state(
        ref_base_dir=base_dir,
        ref_chain=ref_chain,
    )