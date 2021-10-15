"""
sbu.dataframe_postprocess
=========================

A module for creating new dataframes from the SBU-containing dataframe.

Index
-----
.. currentmodule:: sbu.dataframe_postprocess
.. autosummary::
    get_sbu_per_project
    get_agregated_sbu
    get_percentage_sbu
    _get_active_name

API
---
.. autofunction:: get_sbu_per_project
.. autofunction:: get_agregated_sbu
.. autofunction:: get_percentage_sbu
.. autofunction:: _get_active_name

"""

from typing import Hashable

import numpy as np
import pandas as pd

from sbu.globvar import ACTIVE, NAME, PROJECT, SBU_REQUESTED

__all__ = ['get_sbu_per_project', 'get_agregated_sbu', 'get_percentage_sbu']


def get_sbu_per_project(df: pd.DataFrame) -> pd.DataFrame:
    """Construct a new Pandas DataFrame with SBU usage per project.

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A Pandas DataFrame with SBU usage per username, constructed by :func:`get_sbu`.
        :attr:`pandas.DataFrame.columns` and :attr:`pandas.DataFrame.index` should be
        instances of :class:`pandas.MultiIndex` and :class:`pandas.Index`, respectively.

    Returns
    -------
    :class:`pandas.DataFrame`
        A new Pandas DataFrame holding the SBU usage per project (*i.e.* **df** [**project**]).

    """
    df_tmp = df.set_index(PROJECT, inplace=False)
    df_tmp.index.name = 'project'

    dict_ = {i: ['first' if i[0] == 'info' else sum] for i in df_tmp}
    ret = df_tmp.groupby(df_tmp.index).aggregate(dict_)
    ret.columns = ret.columns.droplevel(2)
    ret[ACTIVE] = [_get_active_name(df_tmp, i) for i in ret.index]
    del ret[NAME]
    return ret


def get_agregated_sbu(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the SBU accumulated over all months in the ``"Month"`` super-column.

    Examples
    --------
    Considering the following DataFrame as input:

    .. code:: python

        >>> print(df['Month'])
                        2019-01  2019-02  2019-03
        username
        Donald Duck      1000.0   1500.0    750.0
        Scrooge McDuck   1000.0    500.0    250.0
        Mickey Mouse     1000.0   5000.0   4000.0

    Which will be accumulated along each column in the following manner:

    .. code:: python

        >>> df_new = get_agregated_sbu(df)
        >>> print(df_new['Month'])
                        2019-01  2019-02  2019-03
        username
        Donald Duck      1000.0   2500.0   3250.0
        Scrooge McDuck   1000.0   1500.0   1750.0
        Mickey Mouse     1000.0   6000.0  10000.0

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A Pandas DataFrame with SBU usage per project, constructed by :func:`get_sbu_per_project`.
        :attr:`pandas.DataFrame.columns` and :attr:`pandas.DataFrame.index` should be
        instances of :class:`pandas.MultiIndex` and :class:`pandas.Index`, respectively.

    Returns
    -------
    :class:`pandas.DataFrame`
        A new Pandas DataFrame with SBU usage accumulated over all columns in the ``"Month"``
        super-column.

    """
    SUM = ('Month', 'sum')
    ret = df.copy()

    del ret[SUM]
    ret['Month'] = np.cumsum(ret['Month'], axis=1)
    ret[SUM] = ret['Month'].iloc[:, -1]
    return ret


def get_percentage_sbu(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the % accumulated SBU usage per project.

    The column storing the requested amount of SBUs can be defined in the global variable
    ``_GLOBVAR["SBU_REQUESTED"]`` (default value: ``("info", "SBU requested")``).

    Examples
    --------
    Considering the following DataFrame with accumulated SBUs as input:

    .. code:: python

        >>> print(df)
                                info   Month
                       SBU requested 2019-01 2019-02  2019-03
        username
        Donald Duck           3250.0  1000.0  2500.0   3250.0
        Scrooge McDuck        5000.0  1000.0  1500.0   1750.0
        Mickey Mouse          5000.0  1000.0  6000.0  10000.0

    Which will result in the following SBU usage:

    .. code:: python

        >>> df_new = get_percentage_sbu(df)
        >>> print(df_new['Month'])
                        2019-01  2019-02  2019-03
        username
        Donald Duck        0.31     0.77     1.00
        Scrooge McDuck     0.20     0.30     0.35
        Mickey Mouse       0.20     1.20     2.00

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A Pandas DataFrame with the accumulated SBU usage per project,
        constructed by :func:`get_agregated_sbu`.
        :attr:`pandas.DataFrame.columns` and :attr:`pandas.DataFrame.index` should be
        instances of :class:`pandas.MultiIndex` and :class:`pandas.Index`, respectively.

    Returns
    -------
    :class:`pandas.DataFrame`
        A new Pandas DataFrame with % SBU usage accumulated over all columns in the ``"Month"``
        super-column.

    """
    ret = df.copy()
    ret['Month'] /= ret[SBU_REQUESTED].values[:, None]
    ret['Month'] = ret['Month'].round(2)
    return ret


def _get_active_name(df: pd.DataFrame, index: Hashable) -> tuple:
    """Return a tuple with the names of all active users."""
    if index == 'sum':
        return ()

    slice_ = df.loc[index, NAME]
    condition = df.loc[index, ACTIVE] == True  # noqa
    if isinstance(slice_, str):
        return (slice_,) if condition else ()
    else:
        return tuple(slice_[condition].tolist())
