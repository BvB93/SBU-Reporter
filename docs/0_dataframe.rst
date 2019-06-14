sbu.dataframe
=============

Index
-----

=================================== ========================================================================================
 Function                            Description
=================================== ========================================================================================
 :func:`.yaml_to_pandas`             Create a Pandas DataFrame out of a .yaml file.
 :func:`.get_sbu`                    Acquire the SBU usage for each account in the :attr:`pandas.DataFrame.index`.
 :func:`.get_sbu_per_project`        Construct a new Pandas DataFrame with SBU usage per project.
 :func:`.get_agregated_sbu`          Calculate the SBU accumulated over all months in the ``"Month"`` super-column.
 :func:`.get_percentage_sbu`         Calculate the % accumulated SBU usage per project.
 :func:`.parse_accuse`               Gather SBU usage of a specific user account.
 :func:`.get_date_range`             Return the start and end date formatted as two strings.
 :func:`.validate_usernames`         Validate that all users belonging to an account are available in the .yaml input file.
 :func:`.construct_filename`         Construct a filename containing the current date.
 :func:`.update_globals`             Update the column names stored in the global variable ``GLOBVAR``.
 :func:`._get_datetimeindex`         Create a Pandas DatetimeIndex from a start and end date.
 :func:`._parse_date`                Parse any dates supplied to :func:`.get_date_range`.
 :func:`._get_total_sbu_requested`   Return the total number of requested SBUs.
 :func:`._get_active_name`           Return a tuple active with names of all active users.
 :func:`._repopulate_globals`        Update the all globally defined column names based on the content of ``_GLOBVAR``.
=================================== ========================================================================================

API
---

.. automodule:: sbu.dataframe
    :members:

.. autofunction:: sbu.dataframe._get_datetimeindex

.. autofunction:: sbu.dataframe._parse_date

.. autofunction:: sbu.dataframe._get_total_sbu_requested

.. autofunction:: sbu.dataframe._get_active_name

.. autofunction:: sbu.dataframe._repopulate_globals
