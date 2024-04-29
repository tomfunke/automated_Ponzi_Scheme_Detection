import pm4py
import pandas as pd
import numpy as np

def convert_df_coloumns(df):
    # Rename the columns to match the OCEL standard
    df.rename(columns={"name": "concept:name"}, inplace=True)#concept:name is the activity
    df.rename(columns={"timeStamp": "time:timestamp"}, inplace=True)
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], dayfirst=False)

    # Directly rename the first column to 'ocel:eid'
    # Assuming the first column is the one without a name -> NUR IN CSV! Aber eigentlich nicht notwendig, die spalte?
    #df.columns.values[0] = 'ocel:eid'

    return df

def safe_preprocessed_file(df, file_path, format_type):
    # Save the preprocessed DataFrame to a new File
    preprocessed_path = file_path.replace(format_type, f'_preprocessed{format_type}')
    if format_type == ".csv":
        df.to_csv(preprocessed_path, index=False)
    elif format_type == ".pkl":
        df.to_pickle(preprocessed_path)

def read_input_file(input_csv_file_path, format_type):
    # Read the CSV or pickle file into a pandas DataFrame
    if format_type == ".csv":
        df = pd.read_csv(input_csv_file_path)
    elif format_type == ".pkl":
        df = pd.read_pickle(input_csv_file_path) #for pickle files
    else:
        raise ValueError("The input file format is not supported")
    
    return df
    

def convert_events_dapp_to_ocel(format_type, file_path, object_selection):
    df = read_input_file(file_path, format_type)
    df = convert_df_coloumns(df)

    # Creates a list of all columns that are additional for the OCEL as event attributes: All Coloumns - the chosen object - the standard columns time and activity
    columns_to_remove = np.array(['concept:name', 'time:timestamp']+object_selection)
    remaining_attributes = np.setdiff1d(df.columns.to_numpy(), columns_to_remove)
    #example_objects = ["user"] # either choose objective via Input here or its always coloumn 9! (user/owner)
    #remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber"] + additional_columns
    
    #converts the dataframe to ocel format with the given object types
    ocel = pm4py.convert_log_to_ocel(df, object_types=object_selection, additional_event_attributes = remaining_attributes)

    safe_preprocessed_file(df, file_path, format_type)
    
    return ocel

def convert_call_dapp_to_ocel(format_type, file_path, object_selection):
    df = read_input_file(file_path, format_type)
    # Remove rows where 'name' is None or ''
    # This is necessary because the OCEL importer does not accept empty activity names: so effectively, we are removing every Error like out of gas
    df = df[df['name'].notna() & (df['name'] != '')]

    #TODO: Kick noch Zeilen mit gleichen Hash, da mehrmals die Zeile da ist bei call_dapp. denn die leeren zuvor gefilterteten, sind die mit einem error,
    # welche in der nächsten zeile auch noch gekickt werden müssen

    convert_df_coloumns(df)

    # Creates a list of all columns that are additional for the OCEL as event attributes: All Coloumns minus the chosen object minus the standard columns time and activity
    remaining_attributes = np.setdiff1d(df.columns.to_numpy(), np.array(['concept:name', 'time:timestamp']+object_selection))
    #object_selection = ["from"] # either choose objective via Input here or its always coloumn 2! "from"
    #remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber", "to", "callvalue", "input", "output", "gas", "gasUsed", "functionName", "error", "calltype"] # hier fehlen noch spalten
    
    #converts the dataframe to ocel format with the given object types
    ocel = pm4py.convert_log_to_ocel(df, object_types=object_selection, additional_event_attributes = remaining_attributes)

    safe_preprocessed_file(df, file_path, format_type)
    
    return ocel
    