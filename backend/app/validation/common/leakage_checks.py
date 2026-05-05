"""Training-pool leakage assertions (validation compound exclusion)."""

from __future__ import annotations

from typing import AbstractSet, Iterable, List, Sequence, Tuple, Protocol


class EntryLike(Protocol):
    compound_id: str


def assert_validation_compounds_absent(
    entries: Sequence[EntryLike],
    train_idx: Sequence[int],
    val_idx: Sequence[int],
    test_idx: Sequence[int],
    validation_compound_ids: AbstractSet[str],
) -> None:
    """Fail fast if any held-out validation compound_id appears in train/val/test index pools."""
    pools: Tuple[str, List[int]] = [
        ("train", list(train_idx)),
        ("val", list(val_idx)),
        ("test", list(test_idx)),
    ]
    for name, idxs in pools:
        for i in idxs:
            cid = entries[i].compound_id
            if cid in validation_compound_ids:
                raise AssertionError(
                    f"Leakage: validation compound_id {cid!r} found in {name} pool (index {i}). "
                    "Exclude validation drugs from all training folds."
                )


def collect_compound_ids(indices: Iterable[int], entries: Sequence[EntryLike]) -> set[str]:
    return {entries[i].compound_id for i in indices}
