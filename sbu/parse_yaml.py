"""
sbu.parse_yaml
==============

A module for parsing and validating the .yaml input.

Index
-----
.. currentmodule:: sbu.parse_yaml
.. autosummary::
    yaml_to_pandas
    validate_usernames

API
---
.. autofunction:: yaml_to_pandas
.. autofunction:: validate_usernames

"""

from subprocess import check_output

from typing import (Tuple, Hashable, Any, Dict, Optional)

import yaml
import numpy as np
import pandas as pd

from sbu.globvar import ACTIVE, NAME, PROJECT, SBU_REQUESTED, TMP

__all__ = ['yaml_to_pandas', 'validate_usernames']


def yaml_to_pandas(filename: str) -> Tuple[pd.DataFrame, Optional[str]]:
    """Create a Pandas DataFrame out of a .yaml file.

    Examples
    --------
    Example yaml input:

    .. code-block:: yaml

        __project__: BlaBla
        A:
            description: Example project
            PI: Walt Disney
            SBU requested: 1000
            users:
                user1: Donald Duck
                user2: Scrooge McDuck
                user3: Mickey Mouse

    Example output:

    .. code-block:: python

        >>> df, project = yaml_to_pandas(filename)

        >>> print(df)
                    info                  ...
                 project            name  ... SBU requested           PI
        username                          ...
        user1          A     Donald Duck  ...        1000.0  Walt Disney
        user2          A  Scrooge McDuck  ...        1000.0  Walt Disney
        user3          A    Mickey Mouse  ...        1000.0  Walt Disney

        >>> print(project)
        BlaBla

    Parameters
    ----------
    filename : :class:`str`
        The path+filename to the .yaml file.

    Returns
    -------
    :class:`pandas.DataFrame` & :class:`str`, optional
        A Pandas DataFrame and project name constructed from **filename**.
        Columns and rows are instances of :class:`pandas.MultiIndex` and
        :class:`pandas.Index`, respectively.
        All retrieved .yaml data is stored under the ``"info"`` super-column.
        The project name will be :data:`None` if the ``__project__`` key is absent
        from the .yaml file

    """
    # Read the yaml file
    with open(filename, 'r') as f:
        dict_ = yaml.load(f, Loader=yaml.SafeLoader)
    project = dict_.pop("__project__", None)

    # Convert the yaml dictionary into a dataframe
    data: Dict[str, Dict[Tuple[Hashable, Hashable], Any]] = {}
    for k1, v1 in dict_.items():
        for k2, v2 in v1['users'].items():
            data[k2] = {('info', k): v for k, v in v1.items() if k != 'users'}
            data[k2][NAME] = v2
            data[k2][PROJECT] = k1
    df = pd.DataFrame(data).T

    # Fortmat, sort and return the dataframe
    df.index.name = 'username'
    df[SBU_REQUESTED] = df[SBU_REQUESTED].astype(float)
    df[TMP] = df.index
    df.sort_values(by=[PROJECT, TMP], inplace=True)
    df.sort_index(axis=1, inplace=True, ascending=False)
    del df[TMP]
    df[ACTIVE] = False

    validate_usernames(df)
    return df, project


def validate_usernames(df: pd.DataFrame) -> None:
    """Validate that all users belonging to an account are available in the .yaml input file.

    Raises a KeyError If one or more usernames printed by the ``accinfo`` comand are absent from
    **df**.

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A DataFrame, produced by :func:`.yaml_to_pandas`, containing user accounts.
        :attr:`pandas.DataFrame.columns` and :attr:`pandas.DataFrame.index`
        should be instances of :class:`pandas.MultiIndex` and :class:`pandas.Index`, respectively.
        User accounts are expected to be stored in :attr:`pandas.DataFrame.index`.

    Raises
    ------
    ValueError
        Raised if one or more users reported by the ``accinfo`` command are absent from **df** or
        *vice versa*.

    """
    _usage = check_output(['accinfo'], encoding='utf8')
    iterator = filter(None, _usage.splitlines())
    for i in iterator:
        if i == "# Users linked to this account":
            usage = np.array(list(iterator), dtype=np.str_)
            break
    else:
        raise ValueError("Failed to parse the passed .yaml file")

    bool_ar1 = np.isin(usage, df.index)
    bool_ar2 = np.isin(df.index, usage)
    name_diff = ""
    name_diff += "".join(f"\n- {name}" for name in usage[~bool_ar1])
    name_diff += "".join(f"\n+ {name}" for name in df.index[~bool_ar2].values)
    if name_diff:
        raise ValueError(f"User mismatch between .yaml file and `accinfo` output:{name_diff}")
