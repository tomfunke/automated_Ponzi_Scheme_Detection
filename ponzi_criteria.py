import pm4py
import pandas as pd

def check_ponzi_criteria(ocel):
    df_ocel = ocel.get_extended_table()
    print(df_ocel)
    return