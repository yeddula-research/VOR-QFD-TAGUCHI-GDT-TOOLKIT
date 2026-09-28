"""Standard Taguchi orthogonal arrays (levels coded 0, 1, 2, ...).

The paper uses an L9 or L18 inner array "depending on the number of control
factors and their levels". L4 and L8 are included for two-level outer
(noise) arrays.
"""

from __future__ import annotations

from itertools import combinations, product

import numpy as np

_L4 = [
    [1, 1, 1],
    [1, 2, 2],
    [2, 1, 2],
    [2, 2, 1],
]

_L8 = [
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 2, 2, 2, 2],
    [1, 2, 2, 1, 1, 2, 2],
    [1, 2, 2, 2, 2, 1, 1],
    [2, 1, 2, 1, 2, 1, 2],
    [2, 1, 2, 2, 1, 2, 1],
    [2, 2, 1, 1, 2, 2, 1],
    [2, 2, 1, 2, 1, 1, 2],
]

_L9 = [
    [1, 1, 1, 1],
    [1, 2, 2, 2],
    [1, 3, 3, 3],
    [2, 1, 2, 3],
    [2, 2, 3, 1],
    [2, 3, 1, 2],
    [3, 1, 3, 2],
    [3, 2, 1, 3],
    [3, 3, 2, 1],
]

# L18 (2^1 x 3^7): column 1 has two levels, columns 2-8 have three.
_L18 = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 2, 2, 2, 2, 2, 2],
    [1, 1, 3, 3, 3, 3, 3, 3],
    [1, 2, 1, 1, 2, 2, 3, 3],
    [1, 2, 2, 2, 3, 3, 1, 1],
    [1, 2, 3, 3, 1, 1, 2, 2],
    [1, 3, 1, 2, 1, 3, 2, 3],
    [1, 3, 2, 3, 2, 1, 3, 1],
    [1, 3, 3, 1, 3, 2, 1, 2],
    [2, 1, 1, 3, 3, 2, 2, 1],
    [2, 1, 2, 1, 1, 3, 3, 2],
    [2, 1, 3, 2, 2, 1, 1, 3],
    [2, 2, 1, 2, 3, 1, 3, 2],
    [2, 2, 2, 3, 1, 2, 1, 3],
    [2, 2, 3, 1, 2, 3, 2, 1],
    [2, 3, 1, 3, 2, 3, 1, 2],
    [2, 3, 2, 1, 3, 1, 2, 3],
    [2, 3, 3, 2, 1, 2, 3, 1],
]

ARRAYS = {"L4": _L4, "L8": _L8, "L9": _L9, "L18": _L18}


def get_array(name: str) -> np.ndarray:
    """Return orthogonal array ``name`` with levels coded from 0."""
    try:
        return np.asarray(ARRAYS[name], dtype=int) - 1
    except KeyError:
        raise ValueError(f"unknown orthogonal array {name!r}; choose from {sorted(ARRAYS)}") from None


def is_orthogonal(array: np.ndarray) -> bool:
    """True if every pair of columns contains each level combination equally often."""
    a = np.asarray(array)
    for i, j in combinations(range(a.shape[1]), 2):
        li, lj = np.unique(a[:, i]), np.unique(a[:, j])
        counts = [np.sum((a[:, i] == x) & (a[:, j] == y)) for x, y in product(li, lj)]
        if len(set(counts)) != 1:
            return False
    return True


def select_inner_array(n_factors: int, n_levels: int = 3) -> str:
    """Pick L9 or L18 for ``n_factors`` three-level control factors.

    L9 holds up to four three-level factors; L18 holds up to seven (plus one
    optional two-level factor in its first column).
    """
    if n_levels != 3:
        raise ValueError("only three-level control factors are supported (L9 / L18)")
    if n_factors < 1:
        raise ValueError("need at least one control factor")
    if n_factors <= 4:
        return "L9"
    if n_factors <= 7:
        return "L18"
    raise ValueError("more than seven three-level factors needs a larger array than L18")


def assign_columns(array_name: str, n_factors: int) -> list[int]:
    """Column indices used for ``n_factors`` three-level factors in ``array_name``."""
    if array_name == "L9":
        cols = [0, 1, 2, 3]
    elif array_name == "L18":
        cols = [1, 2, 3, 4, 5, 6, 7]
    else:
        raise ValueError("inner arrays are L9 or L18")
    if n_factors > len(cols):
        raise ValueError(f"{array_name} cannot hold {n_factors} three-level factors")
    return cols[:n_factors]
