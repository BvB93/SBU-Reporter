from typing import (Tuple, Any, Hashable)

import pandas as pd
import numpy as np


def _get_active_name(df: pd.DataFrame,
                     i: Hashable) -> Tuple[Any]:
    """Return a tuple active names"""
    if i == 'sum':
        return ()
    slice_ = df.loc[i, ('info', 'name')]
    condition = df.loc[i, ('info', 'active')] == True
    return tuple(slice_[condition].tolist())


def get_agregated_sbu(df: pd.DataFrame) -> pd.DataFrame:
    ret = df.copy()
    del ret[('Month', 'sum')]
    ret['Month'] = np.cumsum(ret['Month'], axis=1)
    ret[('Month', 'sum')] = ret['Month'].iloc[:, -1]

    for i, j in df['Month'].items():
        if np.isnan(j).all():
            ret.loc[('Month', i)] = np.nan

    return ret


def get_percentage_sbu(df: pd.DataFrame) -> pd.DataFrame:
    ret = df.copy()
    ret['Month'] /= ret[('info', 'SBU requested')][:, None]
    return ret


filename = '/Users/bvanbeek/Downloads/test_30_May_2019.csv'
df = pd.read_csv(filename, header=[0, 1], index_col=0, float_precision='high')

df.set_index(('info', 'project'), inplace=True)
df.index.name = 'project'
# del df['info']
# df.columns = df.columns.droplevel(0)

dict_ = {i: ['first' if i[0] == 'info' else sum] for i in df}
ret = df.groupby(df.index).aggregate(dict_)
ret.columns = ret.columns.droplevel(2)
ret[('info', 'active')] = [_get_active_name(df, i) for i in ret.index]
del ret[('info', 'name')]
del ret[('info', 'SBU usage')]
ret.at['sum', ('info', 'SBU requested')] = 31650000.0

a = get_agregated_sbu(ret)
b = get_percentage_sbu(a)
