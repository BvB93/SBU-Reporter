"""
sbu.plot
========

A module for handling data plotting.

Index
-----
.. currentmodule:: sbu.plot
.. autosummary::

    pre_process_df
    pre_process_plt
    post_process_plt

API
---
.. autofunction:: sbu.plot.pre_process_df
.. autofunction:: sbu.plot.pre_process_plt
.. autofunction:: sbu.plot.post_process_plt

"""

from datetime import date
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib as plt

from sbu.globvar import PI

__all__ = ['pre_process_df', 'pre_process_plt', 'post_process_plt']


def pre_process_df(df: pd.DataFrame, percent: bool = False) -> pd.DataFrame:
    """Pre-process a Pandas DataFrame for the purpose of plotting.

    * All columns which do not fall under the ``"Month"`` super-column are removed.
    * The ``("Month", "sum")`` column is removed.
    * The SBU maxima are added to the index.
    * The DataFrame is transposed.

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A DataFrame holding the accumulated SBU usage.
        See :func:`.get_agregated_sbu`.

    percent : :class:`bool`
        If ``True``, multiply all values by 100 and change the data type to :class:`int`.

    Returns
    -------
    :class:`pandas.DataFrame`:
        A newly formatted DataFrame suitable for data plotting.

    """
    ret = df.copy()
    del ret['info']
    del ret[('Month', 'sum')]
    ret.drop('sum', inplace=True)
    ret.drop('None', inplace=True)

    ret.columns = ret.columns.droplevel(0)
    ret.columns.name = 'Month'

    pi_series = df[PI].iloc[:-2]
    idx_name = ret.index.name

    if percent:
        with pd.option_context('mode.use_inf_as_na', True):
            for key, series in ret.items():
                series.fillna(0.0, inplace=True)
                ret[key] = (100 * series).astype(int)
        iterator = zip(pi_series, ret.iterrows())
        ret.index = [f'{project} ({pi}): {np.nanmax(sbu)} %' for pi, (project, sbu) in iterator]
    else:
        iterator = zip(pi_series, ret.iterrows())
        ret.index = [f'{project} ({pi}): {np.nanmax(sbu):,.0f}' for pi, (project, sbu) in iterator]

    ret.index.name = idx_name
    return ret.T


def pre_process_plt(df: pd.DataFrame, ax: Optional[plt.axes.Axes] = None,
                    lineplot_dict: Optional[Dict[str, Any]] = None,
                    overide_dict: Optional[Dict[str, Any]] = None) -> plt.axes.Axes:
    """Create a Matplotlib Axes instance from a Pandas DataFrame.

    Various Seaborn_ arguments can be supplied via **lineplot_dict** and **overide_dict**.

    .. _Seaborn: https://seaborn.pydata.org/

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A DataFrame holding the accumulated SBU usage.
        See :func:`pre_process_df` and :func:`.get_agregated_sbu`.

    ax : :class:`matplotlib.Axes<matplotlib.axes.Axes>`, optional
        An optional Axes instance for :func:`seaborn.lineplot`.

    lineplot_dict : :class:`dict`, optional
        Various keyword arguments for :func:`seaborn.lineplot`.

    overide_dict : :class:`dict`, optional
        Various keyword arguments for the ``rc`` argument in :func:`seaborn.set_style`.

    Return
    ------
    :class:`matplotlib.axes.Axes`:
        An Axes instance constructed from **df**.

    """
    # Clip certain values in **lineplot_dict** te ensure they are of equal length as **df**
    if lineplot_dict is not None:
        clip_tup = ('palette', 'dashes', 'markers')
        clip_slice = slice(0, len(df.columns))
        for i in clip_tup:
            if i in lineplot_dict:
                lineplot_dict[i] = lineplot_dict[i][clip_slice]

    sns.set(font_scale=1.2)
    sns.set(rc={'figure.figsize': (10.0, 6.0)})
    sns.set_style(style='ticks', rc=overide_dict)

    return sns.lineplot(data=df, ax=ax, **lineplot_dict)


def post_process_plt(df: pd.DataFrame, ax: plt.axes.Axes,
                     percent: bool = False) -> plt.figure.Figure:
    """Post-process the Matplotlib Axes instance produced by :func:`pre_process_plt`.

    The post-processing invovles further formatting of the legend, the x-axis and the y-axis.

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A DataFrame holding the accumulated SBU usage.
        See :func:`pre_process_df` and :func:`.get_agregated_sbu`.

    ax : :class:`matplotlib.Axes<matplotlib.axes.Axes>`
        An Axes instance produced by :func:`pre_process_plt`.

    percent : class`bool`
        If ``True``, apply additional formatting for handling percentages.

    Returns
    -------
    :class:`matplotlib.figure.Figure`:
        A Matplotlib Figure constructed from **ax**.

    """
    df_max = df.max().max()
    decimals = 1 - len(str(int(df.values.max())))
    y_max = round(df_max, decimals) + 10**-decimals

    # Format the y-axis
    ax.yaxis.set_major_formatter(plt.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.set(ylim=(0, y_max))

    # Format the x-axis
    i = len(df.index) // 6 or 1
    ax.set(xticks=df.index[0::i])

    today = date.today().strftime('%d %b %Y')
    if percent:
        ax.set_ylabel('SBUs (System Billing Units)  /  %')
        ax.set_title('Accumulated % SBU usage: {}'.format(today), fontdict={'fontsize': 18})
        ax.legend_.set_title('Project (PI): % SBU')
    else:
        ax.set_ylabel('SBUs (System Billing Units)  /  hours')
        ax.set_title('Accumulated SBU usage: {}'.format(today), fontdict={'fontsize': 18})
        ax.legend_.set_title('Project (PI): SBU')
    return ax.get_figure()
