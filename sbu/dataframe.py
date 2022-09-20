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

import re
import datetime
from subprocess import check_output
from typing import Tuple, Optional, Union

import numpy as np
import pandas as pd

from sbu.globvar import ACTIVE, PROJECT, SBU_REQUESTED

__all__ = [
    'get_date_range', 'construct_filename', 'get_sbu', 'parse_accuse'
]


def get_sbu(
    df: pd.DataFrame,
    project: str,
    start: Union[None, str, int] = None,
    end: Union[None, str, int] = None,
) -> None:
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

    df_tmp = parse_accuse(project, sy, ey)
    df.update(df_tmp)

    # Calculate SBU sums
    SUM = ('Month', 'sum')
    df[SUM] = df['Month'].sum(axis=1)
    nan_template = {k: np.nan for k in df.columns}
    nan_template['info', 'active'] = False
    df.loc['sum'] = nan_template
    df.loc['sum', 'Month'] = df['Month'].sum(axis=0).values
    df.at['sum', PROJECT] = 'sum'
    df.at['sum', SBU_REQUESTED] = _get_total_sbu_requested(df)

    # Mark all active users
    df[ACTIVE] = False
    df.loc[df[SUM] > 1.0, ACTIVE] = True


DATE_PATTERN = re.compile("([0-9]+)-([0-9][0-9])-?([0-9][0-9])?")


def parse_accuse(
    project: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Gather SBU usage of a specific user account.

    The bash command ``accuse`` is used for gathering SBU usage along an interval defined
    by **start** and **end**.
    Results are collected and returned in a Pandas DataFrame.

    Parameters
    ----------
    project : :class:`str`
        The project code of the project of interest.

    start : :class:`str`
        The starting date of the interval.
        Accepts dates formatted as YYYY, MM-YYYY or DD-MM-YYYY.

    end : :class:`str`
        The final date of the interval.
        Accepts dates formatted as YYYY, MM-YYYY or DD-MM-YYYY.

    Returns
    -------
    :class:`pandas.DataFrame`
        The SBU usage of **user** over a specified period.

    """
    # Acquire SBU usage
    arg = ['accuse', '-a', project]
    if start is not None:
        arg += ["-s", start]
    if end is not None:
        arg += ["-e", end]

    usage = check_output(arg).decode('utf-8')
    usage_list = []
    for i in usage.splitlines():
        try:
            month, *fields = i.split()
        except ValueError:
            continue
        if DATE_PATTERN.fullmatch(month):
            usage_list.append((month, *fields))

    df = pd.DataFrame(usage_list, columns=["Month", "Account", "User", "SBUs", "Restituted"])
    df.set_index("User", inplace=True)
    df["SBUs"] = pd.to_timedelta(df["SBUs"]).astype("m8[s]")
    df["SBUs"] -= pd.to_timedelta(df["Restituted"]).astype("m8[s]")
    df["SBUs"] /= 60**2  # seconds to hours

    index = pd.Index(sorted(set(df.index)), name="username")
    columns = pd.MultiIndex.from_product([
        ["Month"],
        sorted(set(df["Month"]), key=lambda i: np.datetime64(i, "M")),
    ])

    ret = pd.DataFrame(np.nan, index=index, columns=columns)
    for name, (sbu, month) in df[["SBUs", "Month"]].iterrows():
        ret.loc[name, ("Month", month)] = sbu
    return ret


def _get_last_day_of_month(any_day: datetime.date) -> str:
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    ret = next_month - datetime.timedelta(days=next_month.day)
    return ret.strftime('%d')


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
    today = datetime.date.today()
    month = today.strftime('%m')
    year = today.strftime('%Y')
    last_day = _get_last_day_of_month(today)

    start = _parse_date(start, default_month='01', default_year=year)
    end = _parse_date(end, default_day=last_day, default_month=month, default_year=year)

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
    today = datetime.date.today()
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
                default_day: str = '01',
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
        default_year = datetime.date.today().strftime('%Y')

    if input_date is None:
        return f'{default_day}-{default_month}-{default_year}'
    elif isinstance(input_date, int):
        return f'01-01-{input_date}'
    elif isinstance(input_date, str):
        dash_count = input_date.count('-')
        if dash_count == 0:
            return f'{default_day}-{default_month}-{input_date}'
        elif dash_count == 1:
            return f'{default_day}-{input_date}'
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
