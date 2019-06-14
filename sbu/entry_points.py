#!/usr/bin/env python
"""Entry points for SBU-Reporter."""

import argparse
from os.path import isfile
from typing import (List, Optional)

import matplotlib as plt

import sbu

__all__: list = []


def main_sbu(args: Optional[List[str]] = None) -> None:
    """ """
    parser = argparse.ArgumentParser(
        prog='sbu',
        usage='get_sbu <filename> --project <projectname> --startyear <YYYY> --endyear <YYYY>',
        description="Generate and parse all SBU information."
    )

    parser.add_argument(
        'filename', nargs=1, type=str, metavar='<filename>',
        help='A .yaml file with project and account information.'
    )

    parser.add_argument(
        '-p', '--project', type=str, default=[None], required=False, nargs=1, dest='project',
        metavar='<projectname>',
        help='The starting year of the interval. Defaults to the current year.'
    )

    parser.add_argument(
        '-sy', '--startyear', type=int, default=[None], required=False, nargs=1, dest='startyear',
        metavar='<YYYY>', help='The starting year of the interval. Defaults to the current year.'
    )

    parser.add_argument(
        '-ey', '--endyear', type=int, default=[None], required=False, nargs=1, dest='endyear',
        metavar='<YYYY>', help='The final year of the interval. Defaults to <startyear> + 1.'
    )

    args_parsed = parser.parse_args(args)
    filename = args_parsed.filename[0]
    project = args_parsed.project[0]
    startyear = args_parsed.startyear[0]
    endyear = args_parsed.endyear[0]

    if not isfile(filename):
        raise FileNotFoundError("[Errno 2] No such file: '{}'".format(filename))

    sbu_workflow(filename, project, startyear, endyear)


def sbu_workflow(filename: str,
                 project: Optional[str],
                 start: Optional[int],
                 end: Optional[int]) -> None:
    """ """
    df1 = sbu.yaml_to_pandas(filename)
    sbu.get_sbu(df1, start, end, project)
    df2 = sbu.get_sbu_per_project(df1)
    df3 = sbu.get_agregated_sbu(df2)
    df4 = sbu.get_percentage_sbu(df3)

    df_plot = sbu.pre_process_df(df3)
    ax = sbu.pre_process_plt(df_plot, sbu.lineplot_dict, sbu.style_overide)
    fig = sbu.post_process_plt(df_plot, ax)
    plt.show()

    filename = sbu.construct_filename('Cluster_usage', '.{}')
    plt.savefig(filename.format('png'))
    df1.to_csv(filename.format('1.csv'))
    df2.to_csv(filename.format('2.csv'))
    df3.to_csv(filename.format('3.csv'))
    df4.to_csv(filename.format('4.csv'))
