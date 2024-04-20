import pm4py
import pandas as pd

def convert_df_coloumns(df):
    # Rename the columns to match the OCEL standard
    df.rename(columns={"name": "concept:name"}, inplace=True)#concept:name is the activity
    df.rename(columns={"timeStamp": "time:timestamp"}, inplace=True)
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], dayfirst=False)

    # Directly rename the first column to 'ocel:eid'
    # Assuming the first column is the one without a name
    df.columns.values[0] = 'ocel:eid'

    return df

def safe_preprocess_csv(df, csv_file_path):
    # Save the preprocessed DataFrame to a new CSV
    preprocessed_csv_path = csv_file_path.replace('.csv', '_preprocessed.csv')
    df.to_csv(preprocessed_csv_path, index=False)

def convert_events_dapp_to_ocel(csv_file_path):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file_path)
    convert_df_coloumns(df)
    
    # Filter the attributes
    # Check if there are more than 9 columns
    if len(df.columns) > 9:
        # Get all column names after the 9th column
        additional_columns = df.columns[9:].tolist()
    
    example_objects = ["user"] # either choose objective via Input here or its always coloumn 9! (user/owner)
    remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber"] + additional_columns
    #remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber", "referrer", "matrix", "level", "place", "userId", "referrerId", "currentReferrer", "caller", "receiver", "from"]
    
    #converts the dataframe to ocel format with the given object types
    ocel = pm4py.convert_log_to_ocel(df, object_types=example_objects, additional_event_attributes = remaining_attributes)

    safe_preprocess_csv(df, csv_file_path)
    
    return ocel

def convert_call_dapp_to_ocel(csv_file_path):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file_path)

    # Remove rows where 'name' is None or ''
    # This is necessary because the OCEL importer does not accept empty activity names: so effectively, we are removing every Error like out of gas
    df = df[df['name'].notna() & (df['name'] != '')]

    convert_df_coloumns(df)

    example_objects = ["from"] # either choose objective via Input here or its always coloumn 9! (user/owner)
    remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber", "to", "callvalue", "input", "output", "gas", "gasUsed", "functionName", "error", "revertReason"] 
    
    #converts the dataframe to ocel format with the given object types
    ocel = pm4py.convert_log_to_ocel(df, object_types=example_objects, additional_event_attributes = remaining_attributes)

    safe_preprocess_csv(df, csv_file_path)
    
    return ocel
    