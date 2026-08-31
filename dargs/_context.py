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