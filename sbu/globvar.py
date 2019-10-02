"""
sbu.globvar
===========

A module for storing aliases for column keys.

Index
-----
.. currentmodule:: sbu.globvar
.. autosummary::
    update_globals
    _populate_globals

API
---
.. autofunction:: update_globals
.. autofunction:: _populate_globals

"""

from typing import Tuple, Hashable, Dict

__all__ = ['update_globals', 'ACTIVE', 'NAME', 'PI', 'PROJECT', 'SBU_REQUESTED', 'TMP']


def _by_values(tup: Tuple[Hashable, Hashable]) -> Hashable:
    """Take a tuple and return its last value, lowering it if possible (*i.e.* it's a string)."""
    ret = tup[-1]
    try:
        return ret.lower()
    except AttributeError:
        return ret


# Define mandatory columns
_SUPER: str = 'info'
_GLOBVAR: Dict[str, Tuple[Hashable, Hashable]] = {
    'ACTIVE': (_SUPER, 'active'),
    'NAME': (_SUPER, 'name'),
    'PI': (_SUPER, 'PI'),
    'PROJECT': (_SUPER, 'project'),
    'SBU_REQUESTED': (_SUPER, 'SBU requested'),
    'TMP': (_SUPER, 'tmp')
}

# The keys of mandatory dataframe columns
ACTIVE, NAME, PI, PROJECT, SBU_REQUESTED, TMP = sorted(_GLOBVAR.values(), key=_by_values)


def update_globals(column_dict: Dict[str, Tuple[Hashable, Hashable]]) -> None:
    """Update the column names stored in the global variable ``_GLOBVAR``.

    Parameters
    ----------
    column_dict: :class:`dict` [:class:`str`, :class:`tuple` [:class:`Hashable`, :class:`Hashable`]]
        A dictionary which maps column names, present in ``_GLOBVAR``, to new values.
        Tuples, consisting of two hashables,
        are expected as values (*e.g.* ``("info", "new_name")``).
        The following keys (and default values) are available in ``_GLOBVAR``:

        ===================== ==============================
         Key                   Value
        ===================== ==============================
         ``"ACTIVE"``          ``("info", "active")``
         ``"NAME"``            ``("info", "name")``
         ``"PI"``              ``("info", "PI")``
         ``"PROJECT"``         ``("info", "project")``
         ``"SBU_REQUESTED"``   ``("info", "SBU requested")``
         ``"TMP"``             ``("info", "tmp")``
        ===================== ==============================

    Raises
    ------
    TypeError
        Raised if a value in **column_dict** does not consist of a tuple of hashables.

    ValueError
        Raised if the length of a value in **column_dict** is not equal to ``2``.

    """
    for k, v in column_dict.items():
        name = v.__class__.__name__
        if not isinstance(v, tuple):
            raise TypeError(f"Invalid type: '{name}'. "
                            "A 'tuple' consisting of two hashables was expected.")
        elif len(v) != 2:
            raise ValueError(f"Invalid tuple length: '{len(v):d}'. '2' hashables were expected.")
        elif not isinstance(v[0], Hashable) or not isinstance(v[1], Hashable):
            raise TypeError(f"Invalid type: '{name}'. A hashable was expected.")

    for k, v in column_dict.items():
        _GLOBVAR[k] = v
    _populate_globals()


def _populate_globals() -> None:
    """Update the all globally defined column names based on the content of :data:`_GLOBVAR`."""
    global ACTIVE
    global NAME
    global PI
    global PROJECT
    global SBU_REQUESTED
    global TMP

    ACTIVE, NAME, PI, PROJECT, SBU_REQUESTED, TMP = sorted(_GLOBVAR.values(), key=_by_values)
