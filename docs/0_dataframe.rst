sbu.dataframe
=============

Index
-----

============================= ================================================================================
 Function                      Description
============================= ================================================================================
 :func:`.yaml_to_pandas`       Create a Pandas DataFrame out of a .yaml file.
 :func:`.get_sbu`              Acquire the SBU usage for each account in the **df.index**.
 :func:`.get_sbu_per_project`  Construct a new Pandas DataFrame with SBU usage per project.
 :func:`.get_agregated_sbu`    Calculate the SBU accumulated over all months in the ``"Month"`` super-column.
 :func:`.get_percentage_sbu`   Calculate the % accumulated SBU usage per project.
 :func:`.get_date_range`       Return the start and end date formatted as two strings.
 :func:`.construct_filename`   Construct a filename containing the current date.
 :func:`.update_globals`       Update the column names stored in the global variable ``GLOBVAR``.
============================= ================================================================================

API
---

.. automodule:: sbu.dataframe
    :members:

