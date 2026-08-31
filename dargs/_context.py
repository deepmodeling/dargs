"""Internal state shared by dargs tree traversals."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class TraversalContext:
    """Carry operation-scoped state while walking an argument tree.

    Keeping path-sensitive options together prevents individual traversal
    helpers from silently dropping state when they recurse into child
    arguments. The reference chain is immutable so sibling branches do not
    accidentally look like cyclic references to one another.
    """

    allow_ref: bool = False
    trim_pattern: str | None = None
    ref_base_dir: str | None = None
    ref_chain: tuple[str, ...] = ()
    # Mapping identities retain the source context of values merged from a
    # reference.  This lets local overrides resolve independently while still
    # detecting cycles through mappings that actually came from a referenced
    # file.
    ref_origins: tuple[tuple[int, str | None, tuple[str, ...]], ...] = ()

    def for_mapping(self, mapping: object) -> TraversalContext:
        """Return the context associated with ``mapping`` when known.

        A single merged dictionary can contain values from several sources:
        keys supplied locally and keys loaded from ``$ref``.  Traversal uses
        this mapping-specific provenance to select the correct base directory
        and active reference ancestry for each nested mapping.

        Returns
        -------
        TraversalContext
            A context using the mapping-specific reference state when known.
        """
        mapping_id = id(mapping)
        for origin_id, base_dir, ref_chain in reversed(self.ref_origins):
            if origin_id == mapping_id:
                return replace(
                    self,
                    ref_base_dir=base_dir,
                    ref_chain=ref_chain,
                )
        return self

    def with_mapping_origins(
        self,
        origins: dict[int, tuple[str | None, tuple[str, ...]]],
    ) -> TraversalContext:
        """Return a context extended with mapping provenance entries.

        Returns
        -------
        TraversalContext
            A context containing the supplied provenance in addition to the
            existing entries.
        """
        if not origins:
            return self
        merged = {
            origin_id: (base_dir, ref_chain)
            for origin_id, base_dir, ref_chain in self.ref_origins
        }
        merged.update(origins)
        return replace(
            self,
            ref_origins=tuple(
                (origin_id, base_dir, ref_chain)
                for origin_id, (base_dir, ref_chain) in merged.items()
            ),
        )

    def with_ref_state(
        self,
        *,
        ref_base_dir: str,
        ref_chain: tuple[str, ...],
    ) -> TraversalContext:
        """Return a child context with updated reference resolution state.

        Returns
        -------
        TraversalContext
            A context carrying the supplied reference state.
        """
        return replace(
            self,
            ref_base_dir=ref_base_dir,
            ref_chain=ref_chain,
        )
