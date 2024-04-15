import pm4py
import pandas as pd

def convert_events_dapp_to_ocel(csv_file_path):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file_path)

    # Rename the columns to match the OCEL standard
    df.rename(columns={"name": "concept:name"}, inplace=True)
    df.rename(columns={"timeStamp": "time:timestamp"}, inplace=True)
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], dayfirst=False)

    # Directly rename the first column to 'ocel:eid'
    # Assuming the first column is the one without a name
    df.columns.values[0] = 'ocel:eid'
    
    #converts the dataframe to ocel format with the given object types
    example_objects = ["user"]
    remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber", "referrer", "matrix", "level", "place", "userId", "referrerId", "currentReferrer", "caller", "receiver", "from"]
    ocel = pm4py.convert_log_to_ocel(df, object_types=example_objects, additional_event_attributes = remaining_attributes)

    # Save the preprocessed DataFrame to a new CSV to use with pm4py's OCEL importer
    preprocessed_csv_path = csv_file_path.replace('.csv', '_preprocessed.csv')
    df.to_csv(preprocessed_csv_path, index=False)
    
    return ocel