#!/usr/bin/env python
"""
sbu.entry_points
================

Entry points for SBU-Reporter.

Index
-----
.. currentmodule:: sbu.entry_points
.. autosummary::
    main_sbu
    sbu_workflow

API
---
.. autofunction:: main_sbu
.. autofunction:: sbu_workflow

"""

import argparse
from os.path import isfile
from typing import (List, Optional)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sbu


def main_sbu(args: Optional[List[str]] = None) -> None:
    """ """
    parser = argparse.ArgumentParser(
        prog='sbu',
        usage='get_sbu <filename> --project <projectname> --start <start> --end <end>',
        description="Generate and parse all SBU information."
    )

    parser.add_argument(
        'filename', nargs=1, type=str, metavar='<filename>',
        help='A .yaml file with project and account information.'
    )

    parser.add_argument(
        '-p', '--project', type=str, default=[None], required=False, nargs=1, dest='project',
        metavar='<projectname>',
        help='The name of the project of interest.'
    )

    parser.add_argument(
        '-s', '--start', type=str, default=[None], required=False, nargs=1, dest='start',
        metavar='<start>',
        help=('The starting date of the interval. '
              'Accepts input formatted as YYYY, MM-YYYY or DD-MM-YYYY. '
              'Defaults to the start of the current year if left empty.')
    )

    parser.add_argument(
        '-e', '--end', type=str, default=[None], required=False, nargs=1, dest='end',
        metavar='<end>',
        help=('The final date of the interval. '
              'Accepts input formatted as YYYY, MM-YYYY or DD-MM-YYYY. '
              'Defaults to current date if left empty.')
    )

    args_parsed = parser.parse_args(args)
    filename = args_parsed.filename[0]
    project = args_parsed.project[0]
    start = args_parsed.start[0]
    end = args_parsed.end[0]

    if not isfile(filename):
        raise FileNotFoundError("[Errno 2] No such file: '{}'".format(filename))

    sbu_workflow(filename, project, start, end)


def sbu_workflow(filename: str, project: Optional[str],
                 start: Optional[int], end: Optional[int]) -> None:
    """ """
    # Generate the dataframes
    df1 = sbu.yaml_to_pandas(filename)
    sbu.get_sbu(df1, start, end, project)
    df2 = sbu.get_sbu_per_project(df1)
    df3 = sbu.get_agregated_sbu(df2)
    df4 = sbu.get_percentage_sbu(df3)
    file_out = sbu.construct_filename('Cluster_usage', '.{}')

    # Create export figures (.png)
    df_plot = sbu.pre_process_df(df3)
    ax = sbu.pre_process_plt(df_plot, sbu.lineplot_dict, sbu.style_overide)
    fig = sbu.post_process_plt(df_plot, ax)
    plt.savefig(file_out.format('png'), dpi=300, format='png', quality=100, transparent=True)

    # Create and export spreadsheets (.xlsx)
    for df in (df2, df3, df4):
        df[('info', 'active')] = [', '.join(i) for i in df[('info', 'active')]]
    for df in (df1, df2, df3, df4):
        df['Month'] = df['Month'].fillna(0)
        df.replace(np.inf, 0, inplace=True)
        df['Month'] = df['Month'].astype(int)
        df.loc[''] = np.nan
        df.loc[' '] = np.nan
    df_concat = pd.concat([df1, df2, df3, df4])
    df_concat.to_excel(file_out.format('xlsx'), inf_rep='', freeze_panes=(2, 1))

    plt.show(block=True)
