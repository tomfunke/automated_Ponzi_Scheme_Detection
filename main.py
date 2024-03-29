import pm4py
import pandas as pd

def preprocess_and_convert_to_ocel(csv_file_path, mapping):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file_path)
    
    # Directly rename the first column to 'ocel:eid'
    # Assuming the first column is the one without a name
    df.columns.values[0] = 'ocel:eid'
    
    # Rename columns based on the provided mapping
    df_renamed = df.rename(columns=mapping)
    
    # Save the preprocessed DataFrame to a new CSV to use with pm4py's OCEL importer
    preprocessed_csv_path = csv_file_path.replace('.csv', '_preprocessed.csv')
    df_renamed.to_csv(preprocessed_csv_path, index=False)
    
    return preprocessed_csv_path


def main():
    # Path to your OCEL log file (JSON or XML format)
    csv_file_path = '/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000.csv'
    
    # Mapping of original column names to OCEL standard names
    mapping = {
        'timeStamp': 'ocel:timestamp',
        'name': 'ocel:activity',
        'address': 'ocel:type:adress',
        # Add more mappings as needed
    }

    # Preprocess the CSV and get the path to the preprocessed version
    preprocessed_csv_path = preprocess_and_convert_to_ocel(csv_file_path, mapping)
    
    # Assuming the rest of the data is compatible with OCEL, use pm4py to read the preprocessed log
    #event_log = pm4py.read_ocel(preprocessed_csv_path)
    print("done!")

if __name__ == "__main__":
    main()
