import pandas as pd
import numpy as np


def subsetpandas_byvalues(df, initpos, endpos, column_num, addinitrow=1, delendrow=1):
    """subset a pandas dataframe using rows reference"""

    pos1 = df.iloc[:, column_num] == initpos
    if endpos == "end_table":
        endnumberpos = len(df.index) - delendrow
    else:
        pos2 = df.iloc[:, column_num] == endpos

        endnumberpos = np.nonzero(pos2.values)[0][0] - delendrow

    subsetfactors = df.loc[np.nonzero(pos1.values)[0][0] + addinitrow:endnumberpos]
    column_names = subsetfactors.iloc[0]
    subsetfactors = subsetfactors.iloc[1:]
    subsetfactors.columns = column_names

    return (subsetfactors.iloc[:, 1:].reset_index(drop=True))

