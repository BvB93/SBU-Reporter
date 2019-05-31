"""A module which handling the main functionalies of this package."""

from subprocess import check_output
from datetime import date
from typing import (Tuple, Optional, Union, Hashable, Any)

import yaml
import numpy as np
import pandas as pd

__all__ = ['yaml_to_pandas', 'get_date_range', 'construct_filename', 'get_sbu']


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
    :class:`pd.DataFrame`:
        A Pandas DataFrame constructed from **filename**.
        Columns and rows are instances of :class:`pd.MultiIndex` and :class:`pd.Index`,
        respectively.
        All retrieved .yaml data is stored under the ``"info"`` super-column.

    """
    # Read the yaml file
    with open(filename, 'r') as f:
        dict_ = yaml.load(f, Loader=yaml.FullLoader)

    # Convert the yaml dictionary into a dataframe
    pre_df = {}
    for k1, v1 in dict_.items():
        for k2, v2 in v1['users'].items():
            pre_df[k2] = {('info', k): v for k, v in v1.items() if k != 'users'}
            pre_df[k2][('info', 'name')] = v2
            pre_df[k2][('info', 'project')] = k1
    df = pd.DataFrame(pre_df).T

    # Fortmat, sort and return the dataframe
    df.index.name = 'username'
    df[('info', 'SBU requested')] = df[('info', 'SBU requested')].astype(float, copy=False)
    df[('info', 'idx')] = df.index
    df.sort_values(by=[('info', 'project'), ('info', 'idx')], inplace=True)
    df.sort_index(axis=1, inplace=True, ascending=False)
    del df[('info', 'idx')]

    return df


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

    Paramaters
    ----------
    prefix : :class:`str`
        A prefix for the to-be returned filename.
        The current date will be appended to this prefix.

    sufix : :class:`str`
        An optional sufix of the to be returned filename.

    Returns
    -------
    :class:`str`:
        A filename consisting of **prefix** and the current date.

    """
    today = date.today()
    suffix = suffix or ''
    return prefix + today.strftime('_%d_%b_%Y') + suffix


def get_sbu(df: pd.DataFrame,
            start: Optional[int] = None,
            end: Optional[int] = None) -> None:
    """Acquire the SBU usage for each account in the **df.index**.

    The start and end of the reported interval can, optionally, be altered with **start**
    and **end**.
    Performs an inplace update of **df**, adding new columns to hold the SBU usage per month under
    the ``"Month'`` super-column.
    In addition, a single row and column is added (``"sum"``) with SBU usage summed over
    the entire interval and over all users, respectively.

    Parameters
    ----------
    df : :class:`pd.DataFrame`
        A Pandas DataFrame with usernames and information, constructed by :func:`yaml_to_pandas`.
        **df.columns** and **df.index** should be instances of :class:`pd.MultiIndex`
        and :class:`pd.Index`, respectively.
        User accounts are expected to be stored in **df.index**.
        SBU usage (including the sum) is stored in the ``"Month"`` super-column.

    start : :class:`int` or :class:`str`
        The starting year of the interval.
        Defaults to the current year if ``None``.

    end : :class:`str` or :class:`int`
        The final year of the interval.
        Defaults to :code:`start + 1` if ``None``.

    """
    # Construct new columns in **df**
    start, end = get_date_range(start, end)
    date_range = pd.date_range(start, end, freq=pd.offsets.MonthBegin(), name='Month')
    for i in date_range:
        df[('Month', str(i)[:7])] = np.nan

    for u in df.index:
        # Acquire SBU usage
        usage = check_output(
            ['accuse', '-u', u, '-sy', start, '-ey', end]
        ).decode('utf-8').splitlines()

        # Cast SBU usage into a dataframe
        usage = [i.split() for i in usage[2:-1]]
        df_tmp = pd.DataFrame(usage[1:], columns=usage[0])
        df_tmp.drop(0, inplace=True)
        df_tmp.index = pd.MultiIndex.from_product([['Month'], df_tmp['Month']])
        df_tmp.drop(df_tmp.index[df_tmp['Account'] != 'ncvul158'], inplace=True)

        # Parse the actual SBU's
        df_tmp["SBU's"] /= np.timedelta64(1, 's')
        df_tmp['Restituted'] /= np.timedelta64(1, 's')
        df_tmp[u] = df_tmp["SBU's"] - df_tmp['Restituted']
        df_tmp[u] /= 60**2

        # Update **df**
        df.update(df_tmp[[u]].T)

    # Calculate SBU sums
    df[('Month', 'sum')] = df['Month'].sum(axis=1)
    df.loc['sum'] = np.nan
    df.loc['sum', 'Month'] = df['Month'].sum(axis=0).values
    df.at['sum', ('info', 'project')] = 'sum'
    df.at['sum', ('info', 'SBU requested')] = _get_total_sbu_requested(df)

    # Mark all active users
    df[('info', 'active')] = False
    df.loc[df[('Month', 'sum')] > 1.0, ('info', 'active')] = True


def _get_total_sbu_requested(df: pd.DataFrame) -> float:
    """Return the total amount of requested SBUs"""
    slice_ = df[('info', 'SBU requested')]
    return slice_.groupby(slice_.index).aggregate(sum).sum()


def _get_active_name(df: pd.DataFrame,
                     i: Hashable) -> Tuple[Any]:
    """Return a tuple active with names of active users"""
    if i == 'sum':
        return ()
    slice_ = df.loc[i, ('info', 'name')]
    condition = df.loc[i, ('info', 'active')] == True
    return tuple(slice_[condition].tolist())


def get_sbu_per_project(df: pd.DataFrame,
                        project: Hashable = ('info', 'project')) -> pd.DataFrame:
    """Construct a new Pandas DataFrame with SBU usage per project.

    Parameters
    ----------
    df : :class:`pd.DataFrame`
        A Pandas DataFrame with SBU usage per username, constructed by :func:`get_sbu`.
        **df.columns** and **df.index** should be instances of :class:`pd.MultiIndex`
        and :class:`pd.Index`, respectively.

    project : :class:`abc.Hashable`
        The column holding all project names.

    Returns
    -------
    :class:`pd.DataFrame`:
        A new Pandas DataFrame holding the SBU usage per project (*i.e.* **df** [**project**]).

    """
    df_tmp = df.set_index(('info', 'project'), inplace=False)
    df_tmp.index.name = 'project'

    dict_ = {i: ['first' if i[0] == 'info' else sum] for i in df}
    ret = df.groupby(df.index).aggregate(dict_)
    ret.columns = ret.columns.droplevel(2)
    ret[('info', 'active')] = [_get_active_name(df, i) for i in ret.index]
    del ret[('info', 'name')]
    del ret[('info', 'SBU usage')]
    return ret


def get_agregated_sbu(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the SBU accumulated over all months in the ``"Month"`` super-column.

    Parameters
    ----------
    df : :class:`pd.DataFrame`
        A Pandas DataFrame with SBU usage per project, constructed by :func:`get_sbu_per_project`.
        **df.columns** and **df.index** should be instances of :class:`pd.MultiIndex`
        and :class:`pd.Index`, respectively.

    Returns
    -------
    :class:`pd.DataFrame`:
        A new Pandas DataFrame with SBU usage accumulated over all columns in the ``"Month"``
        super-column.
        Empty columns are filled with values of ``np.nan``.

    """
    ret = df.copy()
    del ret[('Month', 'sum')]
    ret['Month'] = np.cumsum(ret['Month'], axis=1)
    ret[('Month', 'sum')] = ret['Month'].iloc[:, -1]

    for i, j in df['Month'].items():
        if np.isnan(j).all():
            ret.loc[('Month', i)] = np.nan

    return ret


def get_percentage_sbu(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the % accumulated SBU usage per project.

    The requested amount of SBUs should be stored in the ``("info", "SBU requested")`` column.

    Parameters
    ----------
    df : :class:`pd.DataFrame`
        A Pandas DataFrame with the accumulated SBU usage per project,
        constructed by :func:`get_agregated_sbu`.
        **df.columns** and **df.index** should be instances of :class:`pd.MultiIndex`
        and :class:`pd.Index`, respectively.

    Returns
    -------
    :class:`pd.DataFrame`:
        A new Pandas DataFrame with % SBU usage accumulated over all columns in the ``"Month"``
        super-column.

    """
    ret = df.copy()
    ret['Month'] /= ret[('info', 'SBU requested')][:, None]
    ret['Month'] *= 100
    return ret


filename = '/Users/bvanbeek/Downloads/test.yaml'
df = yaml_to_pandas(filename)
get_sbu(df)
