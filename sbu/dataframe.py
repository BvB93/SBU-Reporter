"""
sbu.dataframe
=============

A module which handles data parsing and DataFrame construction.

Index
-----
.. currentmodule:: sbu.dataframe
.. autosummary::
    get_sbu
    parse_accuse
    get_date_range
    construct_filename
    _get_datetimeindex
    _parse_date
    _get_total_sbu_requested

API
---
.. autofunction:: get_sbu
.. autofunction:: parse_accuse
.. autofunction:: get_date_range
.. autofunction:: construct_filename
.. autofunction:: _get_datetimeindex
.. autofunction:: _parse_date
.. autofunction:: _get_total_sbu_requested

"""

from subprocess import check_output
from datetime import date
from typing import Tuple, Optional, Union

import numpy as np
import pandas as pd

from sbu.globvar import ACTIVE, PROJECT, SBU_REQUESTED

__all__ = [
    'get_date_range', 'construct_filename', 'get_sbu', 'parse_accuse'
]


def get_sbu(df: pd.DataFrame, start: Union[None, str, int] = None,
            end: Union[None, str, int] = None, project: Optional[str] = None) -> None:
    """Acquire the SBU usage for each account in the :attr:`pandas.DataFrame.index`.

    The start and end of the reported interval can, optionally, be altered with **start**
    and **end**.
    Performs an inplace update of **df**, adding new columns to hold the SBU usage per month under
    the ``"Month'`` super-column.
    In addition, a single row and column is added (``"sum"``) with SBU usage summed over
    the entire interval and over all users, respectively.

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A Pandas DataFrame with usernames and information, constructed by :func:`yaml_to_pandas`.
        :attr:`pandas.DataFrame.columns` and :attr:`pandas.DataFrame.index` should
        be instances of :class:`pandas.MultiIndex` and :class:`pandas.Index`, respectively.
        User accounts are expected to be stored in :attr:`pandas.DataFrame.index`.
        SBU usage (including the sum) is stored in the ``"Month"`` super-column.

    start : :class:`int` or :class:`str`, optional
        Optional: The starting year of the interval.
        Defaults to the current year if ``None``.

    end : :class:`str` or :class:`int`, optional
        Optional: The final year of the interval.
        Defaults to current year + 1 if ``None``.

    project : :class:`str`, optional
        Optional: The project code of the project of interest.
        If not ``None``, only SBUs expended under this project are considered.

    """
    # Construct new columns in **df**
    sy, ey = get_date_range(start, end)
    date_range = _get_datetimeindex(sy, ey)
    for i in date_range:
        df[('Month', str(i)[:7])] = np.nan

    for user in df.index:
        df_user = parse_accuse(user, sy, ey, project)
        df.update(df_user)

    # Calculate SBU sums
    SUM = ('Month', 'sum')
    df[SUM] = df['Month'].sum(axis=1)
    df.loc['sum'] = np.nan
    df.loc['sum', 'Month'] = df['Month'].sum(axis=0).values
    df.at['sum', PROJECT] = 'sum'
    df.at['sum', SBU_REQUESTED] = _get_total_sbu_requested(df)

    # Mark all active users
    df[ACTIVE] = False
    df.loc[df[SUM] > 1.0, ACTIVE] = True


def parse_accuse(user: str, start: str, end: str, project: Optional[str] = None) -> pd.DataFrame:
    """Gather SBU usage of a specific user account.

    The bash command ``accuse`` is used for gathering SBU usage along an interval defined
    by **start** and **end**.
    Results are collected and returned in a Pandas DataFrame.

    Parameters
    ----------
    user : :class:`str`
        A username.

    start : :class:`str`
        The starting date of the interval.
        Accepts dates formatted as YYYY, MM-YYYY or DD-MM-YYYY.

    end : :class:`str`
        The final date of the interval.
        Accepts dates formatted as YYYY, MM-YYYY or DD-MM-YYYY.

    project : :class:`str`, optional
        Optional: The project code of the project of interest.
        If not ``None``, only SBUs expended under this project are considered.

    Returns
    -------
    :class:`pandas.DataFrame`
        The SBU usage of **user** over a specified period.

    """
    # Acquire SBU usage
    arg = ['accuse', '-u', user, '-s', start, '-e', end]
    usage = check_output(arg).decode('utf-8').splitlines()

    # Cast SBU usage into a dataframe
    usage = [i.split() for i in usage[2:-1]]
    df_tmp = pd.DataFrame(usage[1:], columns=usage[0])
    df_tmp.drop(0, inplace=True)
    df_tmp.index = pd.MultiIndex.from_product([['Month'], df_tmp['Month']])
    if project is not None:
        df_tmp.drop(df_tmp.index[df_tmp['Account'] != project], inplace=True)

    # Parse the actual SBU's
    df_tmp["SBU's"] = pd.to_timedelta(df_tmp["SBU's"])
    df_tmp['Restituted'] = pd.to_timedelta(df_tmp["Restituted"])

    # Change the dtype to float
    df_tmp[user] = (df_tmp["SBU's"] - df_tmp['Restituted']).dt.total_seconds()
    df_tmp[user] /= 60**2  # Change seconds into hours
    return df_tmp[[user]].T


def get_date_range(start: Optional[Union[str, int]] = None,
                   end: Optional[Union[str, int]] = None) -> Tuple[str, str]:
    """Return a starting and ending date as two strings.

    Parameters
    ----------
    start : :class:`int` or :class:`str`, optional
        The starting year of the interval.
        Accepts dates formatted as YYYY, MM-YYYY or DD-MM-YYYY.
        Defaults to the current year if ``None``.

    end : :class:`str` or :class:`int`, optional
        The final year of the interval.
        Accepts dates formatted as YYYY, MM-YYYY or DD-MM-YYYY.
        Defaults to the current year + 1 if ``None``.

    Returns
    -------
    :class:`tuple` [:class:`str`, :class:`str`]
        A tuple with the start and end data, formatted as strings.
        Dates are formatted as DD-MM-YYYY.

    """
    today = date.today()
    month = today.strftime('%m')
    year = today.strftime('%Y')

    start = _parse_date(start, default_month='01', default_year=year)
    end = _parse_date(end, default_month=month, default_year=year)

    return start, end


def construct_filename(prefix: str, suffix: Optional[str] = '.csv') -> str:
    """Construct a filename containing the current date.

    Examples
    --------
    .. code:: python

        >>> filename = construct_filename('my_file', '.txt')
        >>> print(filename)
        'my_file_31_May_2019.txt'

    Parameters
    ----------
    prefix : :class:`str`
        A prefix for the to-be returned filename.
        The current date will be appended to this prefix.

    sufix : :class:`str`, optional
        An optional sufix of the to be returned filename.
        No sufix will be attached if ``None``.

    Returns
    -------
    :class:`str`
        A filename consisting of **prefix**, the current date and **suffix**.

    """
    today = date.today()
    suffix = suffix or ''
    return prefix + today.strftime('_%d_%b_%Y') + suffix


def _get_datetimeindex(start: str, end: str) -> pd.DatetimeIndex:
    """Create a Pandas DatetimeIndex from a start and end date.

    Parameters
    ----------
    start : :class:`str`
        The start of the interval.
        Accepts dates formatted as DD-MM-YYYY.

    end : :class:`str`
        The end of the interval.
        Accepts dates formatted as DD-MM-YYYY.

    Returns
    -------
    :class:`pandas.DatetimeIndex`
        A DatetimeIndex starting from **sy** and ending on **ey**.

    """
    _, mm, yyyy = start.split('-')
    start_ = f'{yyyy}-{mm}-01'

    _, mm, yyyy = end.split('-')
    end_ = f'{yyyy}-{mm}-01'

    return pd.date_range(start_, end_, freq=pd.offsets.MonthBegin(), name='Month')


def _parse_date(input_date: Union[str, int, None],
                default_month: str = '01',
                default_year: Optional[str] = None) -> str:
    """Parse any dates supplied to :func:`.get_date_range`.

    Parameters
    ----------
    input_date : :class:`str`, :class:`int` or ``None``
        The to-be parsed date.
        Allowed types and values are:

        * ``None``: Defaults to the first day of the current year and month.
        * :class:`int`: A year (*e.g.* ``2019``).
        * :class:`str`: A date in YYYY, MM-YYYY or DD-MM-YYYY format (*e.g.* ``"22-10-2018"``).

    default_month : :class:`str`
        The default month if a month is not provided in **input_date**.
        Expects a month in MM format.

    default_year : :class:`str`, optional
        Optional: The default year if a year is not provided in **input_date**.
        Expects a year in YYYY format.
        Defaults to the current year if ``None``.

    Returns
    -------
    :class:`str`
        A string, constructed from **input_date**, representing a date in DD-MM-YYYY format.

    Raises
    ------
    ValueError
        Raised if **input_date** is provided as string and contains more than 2 dashes.

    TypeError
        Raised if **input_date** is neither ``None``, a string nor an integer.

    """
    if default_year is None:
        default_year = date.today().strftime('%Y')

    if input_date is None:
        return f'01-{default_month}-{default_year}'
    elif isinstance(input_date, int):
        return f'01-01-{input_date}'
    elif isinstance(input_date, str):
        dash_count = input_date.count('-')
        if dash_count == 0:
            return f'01-{default_month}-{input_date}'
        elif dash_count == 1:
            return f'01-{input_date}'
        elif dash_count == 2:
            return input_date
        else:
            raise ValueError(f"'input_date': '{input_date}'")

    type_name = input_date.__class__.__name__
    raise TypeError(f"The 'input_data' parameter is of invalid type: '{type_name}'")


def _get_total_sbu_requested(df: pd.DataFrame) -> float:
    """Return the total number of requested SBUs."""
    slice_ = df[[SBU_REQUESTED, PROJECT]].iloc[:-1]
    slice_ = slice_.set_index(PROJECT, inplace=False)
    slice_ = slice_.loc[~slice_.index.duplicated(keep='first')]
    return slice_[SBU_REQUESTED].sum()
