"""A module which handles data parsing and DataFrame construction."""

from subprocess import check_output
from datetime import date
from typing import (Tuple, Optional, Union, Hashable, Any, Dict)

import yaml
import numpy as np
import pandas as pd

__all__ = [
    'yaml_to_pandas', 'get_date_range', 'construct_filename', 'get_sbu', 'get_sbu_per_project',
    'get_agregated_sbu', 'get_percentage_sbu', 'update_globals', 'parse_accuse'
]

# Define mandatory columns
SUPER: str = 'info'
GLOBVAR: Dict[str, Tuple[Hashable, Hashable]] = {
    'TMP': (SUPER, 'tmp'),
    'NAME': (SUPER, 'name'),
    'ACTIVE': (SUPER, 'active'),
    'PROJECT': (SUPER, 'project'),
    'SBU_REQUESTED': (SUPER, 'SBU requested')
}

TMP = GLOBVAR['TMP']
NAME = GLOBVAR['NAME']
ACTIVE = GLOBVAR['ACTIVE']
PROJECT = GLOBVAR['PROJECT']
SBU_REQUESTED = GLOBVAR['SBU_REQUESTED']


def yaml_to_pandas(filename: str) -> pd.DataFrame:
    """Create a Pandas DataFrame out of a .yaml file.

    Examples
    --------
    Example yaml input:

    .. code::

        A:
            description: Example project
            PI: Walt Disney
            SBU requested: 1000
            users:
                user1: Donald Duck
                user2: Scrouge McDuck
                user3: Mickey Mouse

    Example output

    .. code:: python

        >>> df = yaml_to_pandas(filename)
        >>> print(type(df))
        <class 'pandas.core.frame.DataFrame'>

        >>> print(df)
                    info                  ...
                 project            name  ... SBU requested           PI
        username                          ...
        user1          A     Donald Duck  ...        1000.0  Walt Disney
        user2          A  Scrouge McDuck  ...        1000.0  Walt Disney
        user3          A    Mickey Mouse  ...        1000.0  Walt Disney

    Parameters
    ----------
    filename : :class:`str`
        The path+filename to the .yaml file.

    Returns
    -------
    :class:`pandas.DataFrame`:
        A Pandas DataFrame constructed from **filename**.
        Columns and rows are instances of :class:`pandas.MultiIndex` and
        :class:`pandas.Index`, respectively.
        All retrieved .yaml data is stored under the ``"info"`` super-column.

    """
    # Read the yaml file
    with open(filename, 'r') as f:
        dict_ = yaml.load(f, Loader=yaml.CLoader)

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
    df[SBU_REQUESTED] = df[SBU_REQUESTED].astype(float, copy=False)
    df[TMP] = df.index
    df.sort_values(by=[PROJECT, TMP], inplace=True)
    df.sort_index(axis=1, inplace=True, ascending=False)
    del df[TMP]
    df[ACTIVE] = False

    return df


def get_sbu(df: pd.DataFrame,
            start: Optional[int] = None,
            end: Optional[int] = None,
            project: Optional[str] = None) -> None:
    """Acquire the SBU usage for each account in the **df.index**.

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
        **df.columns** and **df.index** should be instances of :class:`pandas.MultiIndex`
        and :class:`pandas.Index`, respectively.
        User accounts are expected to be stored in **df.index**.
        SBU usage (including the sum) is stored in the ``"Month"`` super-column.

    start : :class:`int` or :class:`str`
        Optional: The starting year of the interval.
        Defaults to the current year if ``None``.

    end : :class:`str` or :class:`int`
        Optional: The final year of the interval.
        Defaults to :code:`start + 1` if ``None``.

    project : :class:`str`
        Optional: The project code of the project of interest.
        If not ``None``, only SBUs expended under this project are considered.

    """
    # Construct new columns in **df**
    sy, ey = get_date_range(start, end)
    date_range = pd.date_range(start, end, freq=pd.offsets.MonthBegin(), name='Month')
    for i in date_range:
        df[('Month', str(i)[:7])] = np.nan

    for u in df.index:
        df.update(parse_accuse(u, sy, ey, project))

    # Calculate SBU sums
    df[('Month', 'sum')] = df['Month'].sum(axis=1)
    df.loc['sum'] = np.nan
    df.loc['sum', 'Month'] = df['Month'].sum(axis=0).values
    df.at['sum', PROJECT] = 'sum'
    df.at['sum', SBU_REQUESTED] = _get_total_sbu_requested(df)

    # Mark all active users
    df[ACTIVE] = False
    df.loc[df[('Month', 'sum')] > 1.0, ACTIVE] = True


def get_sbu_per_project(df: pd.DataFrame) -> pd.DataFrame:
    """Construct a new Pandas DataFrame with SBU usage per project.

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A Pandas DataFrame with SBU usage per username, constructed by :func:`get_sbu`.
        **df.columns** and **df.index** should be instances of :class:`pandas.MultiIndex`
        and :class:`pandas.Index`, respectively.

    Returns
    -------
    :class:`pandas.DataFrame`:
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
        Scrouge McDuck   1000.0    500.0    250.0
        Mickey Mouse     1000.0   5000.0   4000.0

    Which will be accumulated along each column in the following manner:

    .. code:: python

        >>> df_new = get_agregated_sbu(df)
        >>> print(df_new['Month'])
                        2019-01  2019-02  2019-03
        username
        Donald Duck      1000.0   2500.0   3250.0
        Scrouge McDuck   1000.0   1500.0   1750.0
        Mickey Mouse     1000.0   6000.0  10000.0

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A Pandas DataFrame with SBU usage per project, constructed by :func:`get_sbu_per_project`.
        **df.columns** and **df.index** should be instances of :class:`pandas.MultiIndex`
        and :class:`pandas.Index`, respectively.

    Returns
    -------
    :class:`pandas.DataFrame`:
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
    ``GLOBVAR["SBU_REQUESTED"]`` (default value: ``("info", "SBU requested")``).

    Examples
    --------
    Considering the following DataFrame with accumulated SBUs as input:

    .. code:: python

        >>> print(df)
                                info   Month
                       SBU requested 2019-01 2019-02  2019-03
        username
        Donald Duck           3250.0  1000.0  2500.0   3250.0
        Scrouge McDuck        5000.0  1000.0  1500.0   1750.0
        Mickey Mouse          5000.0  1000.0  6000.0  10000.0

    Which will result in the following SBU usage:

    .. code:: python

        >>> df_new = get_percentage_sbu(df)
        >>> print(df_new['Month'])
                        2019-01  2019-02  2019-03
        username
        Donald Duck        31.0     77.0    100.0
        Scrouge McDuck     20.0     30.0     35.0
        Mickey Mouse       20.0    120.0    200.0

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A Pandas DataFrame with the accumulated SBU usage per project,
        constructed by :func:`get_agregated_sbu`.
        **df.columns** and **df.index** should be instances of :class:`pandas.MultiIndex`
        and :class:`pandas.Index`, respectively.

    Returns
    -------
    :class:`pandas.DataFrame`:
        A new Pandas DataFrame with % SBU usage accumulated over all columns in the ``"Month"``
        super-column.

    """
    ret = df.copy()
    ret['Month'] /= ret[SBU_REQUESTED][:, None]
    ret['Month'] *= 100
    ret['Month'] = ret['Month'].round()
    return ret


def parse_accuse(user: str,
                 start: str,
                 end: str,
                 project: Optional[str] = None) -> pd.DataFrame:
    """Gather SBU usage of a specific user account.

    The bash command ``accuse`` is used for gathering SBU usage along an interval defined
    by **start** and **end**.
    Results are collected and returned in a Pandas DataFrame.

    Parameters
    ----------
    user : :class:`str`
        A username.

    start : :class:`str`
        The starting year of the interval.

    end : :class:`str`
        The final year of the interval.

    project : :class:`str`
        Optional: The project code of the project of interest.
        If not ``None``, only SBUs expended under this project are considered.

    Returns
    -------
    :class:`pandas.DataFrame`:
        The SBU usage of **user** over a specified period.

    """
    # Acquire SBU usage
    arg = ['accuse', '-u', user, '-sy', start, '-ey', end]
    usage = check_output(arg).decode('utf-8').splitlines()

    # Cast SBU usage into a dataframe
    usage = [i.split() for i in usage[2:-1]]
    df_tmp = pd.DataFrame(usage[1:], columns=usage[0])
    df_tmp.drop(0, inplace=True)
    df_tmp.index = pd.MultiIndex.from_product([['Month'], df_tmp['Month']])
    if project is not None:
        df_tmp.drop(df_tmp.index[df_tmp['Account'] != project], inplace=True)

    # Parse the actual SBU's
    df_tmp["SBU's"] /= np.timedelta64(1, 's')
    df_tmp['Restituted'] /= np.timedelta64(1, 's')
    df_tmp[user] = df_tmp["SBU's"] - df_tmp['Restituted']
    df_tmp[user] /= 60**2
    return df_tmp[[user]].T


def get_date_range(start: Optional[Union[str, int]] = None,
                   end: Optional[Union[str, int]] = None) -> Tuple[str, str]:
    """Return a starting and ending date as two strings.

    Parameters
    ----------
    start : :class:`int` or :class:`str`
        The starting year of the interval.
        Defaults to the current year if ``None``.

    end : :class:`str` or :class:`int`
        The final year of the interval.
        Defaults to :code:`start + 1` if ``None``.

    Returns
    -------
    :class:`tuple` [:class:`str`, :class:`str`]
        A tuple with the start and end year, formatted as strings.

    """
    today = date.today()
    start = start or today.strftime('%Y')
    end = end or int(today.strftime('%Y')) + 1
    return str(start), str(end)


def construct_filename(prefix: str,
                       suffix: Optional[str] = '.csv') -> str:
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

    sufix : :class:`str`
        An optional sufix of the to be returned filename.

    Returns
    -------
    :class:`str`:
        A filename consisting of **prefix**, the current date and **suffix**.

    """
    today = date.today()
    suffix = suffix or ''
    return prefix + today.strftime('_%d_%b_%Y') + suffix


def update_globals(column_dict: Dict[str, Tuple[Hashable, Hashable]]) -> None:
    """Update the column names stored in the global variable ``GLOBVAR``.

    Parameters
    ----------
    column_dict: :class:`dict` [:class:`str`, :class:`tuple` [:class:`Hashable`, :class:`Hashable`]]
        A dictionary which maps column names, present in ``GLOBVAR``, to new values.
        Tuples, consisting of two hashables,
        are expected as values (*e.g.* ``("info", "new_name")``).
        The following keys (and default values) are available in ``GLOBVAR``:

        * ``"TMP"``: ``("info", "tmp")``
        * ``"NAME"``: ``("info", "name")``
        * ``"ACTIVE"``: ``("info", "active")``
        * ``"PROJECT"``: ``("info", "project")``
        * ``"SBU_REQUESTED"``: ``("info", "SBU requested")``

    """
    for k, v in column_dict.items():
        if not isinstance(v, tuple):
            err = "Invalid type: '{}'. A 'tuple' consisting of two hashables was expected."
            raise TypeError(err.format(v.__class__.__name__))
        elif len(v) != 2:
            err = "Invalid tuple length: '{:d}'. '2' hashables were expected."
            raise ValueError(err.format(len(v)))
        elif not isinstance(v[0], Hashable) or not isinstance(v[1], Hashable):
            err = "Invalid type: '{}'. A hashable was expected."
            raise TypeError(err.format(v.__class__.__name__))
        GLOBVAR[k] = v


def _get_total_sbu_requested(df: pd.DataFrame) -> float:
    """Return the total amount of requested SBUs."""
    slice_ = df[SBU_REQUESTED]
    return slice_.groupby(slice_.index).aggregate(sum).sum()


def _get_active_name(df: pd.DataFrame,
                     i: Hashable) -> tuple:
    """Return a tuple active with names of active users."""
    if i == 'sum':
        return ()
    slice_ = df.loc[i, NAME]
    condition = df.loc[i, ACTIVE] == True  # noqa
    return tuple(slice_[condition].tolist())