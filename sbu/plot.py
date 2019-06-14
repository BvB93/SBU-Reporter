"""A module for handling data plotting."""

from datetime import date
from typing import (Tuple, Dict, Any, Optional)

import pandas as pd
import seaborn as sns
import matplotlib as plt


__all__ = ['pre_process_df', 'pre_process_plt', 'post_process_plt']

_CLIP: Tuple[str] = ('palette', 'dashes', 'markers')


def pre_process_df(df: pd.DataFrame) -> pd.DataFrame:
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

    idx_name = ret.index.name
    ret.index = ['{}: {:,.0f}'.format(i, j.max()) for i, j in ret.iterrows()]
    ret.index.name = idx_name
    return ret.T


def pre_process_plt(df: pd.DataFrame,
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

    lineplot_dict : :class:`dict`
        Optional: Various keyword arguments for :func:`seaborn.lineplot`.

    overide_dict : :class:`dict`
        Optionasl: Various keyword arguments for the ``rc`` argument in :func:`seaborn.set_style`.

    Return
    ------
    :class:`matplotlib.axes.Axes`:
        An Axes instance constructed from **df**.

    """
    if lineplot_dict is not None:
        clip = len(df.columns)
        for i in _CLIP:
            if i in lineplot_dict:
                lineplot_dict[i] = lineplot_dict[i][0:clip]

    sns.set(font_scale=1.2)
    sns.set(rc={'figure.figsize': (10.0, 6.0)})
    sns.set_style(style='ticks', rc=overide_dict)
    return sns.lineplot(data=df, **lineplot_dict)


def post_process_plt(df: pd.DataFrame,
                     ax: plt.axes.Axes) -> plt.figure.Figure:
    """Post-process the Matplotlib Axes instance produced by :func:`pre_process_plt`.

    The post-processing invovles further formatting of the legend, the x-axis and the y-axis.

    Parameters
    ----------
    df : :class:`pandas.DataFrame`
        A DataFrame holding the accumulated SBU usage.
        See :func:`pre_process_df` and :func:`.get_agregated_sbu`.

    ax: :class:`matplotlib.axes.Axes`
        An Axes instance produced by :func:`pre_process_plt`.

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
    ax.set_ylabel('SBUs (System Billing Units)  /  hours')
    ax.set(ylim=(0, y_max))

    # Format the x-axis
    i = len(df.index) // 6
    ax.set(xticks=df.index[0::i])

    today = date.today().strftime('%d %b %Y')
    ax.set_title('Accumulated SBU usage: {}'.format(today), fontdict={'fontsize': 18})
    ax.legend_.set_title('Project: SBU')
    return ax.get_figure()
