import os
import sys
import json
import pandas as pd
import ethereumnode

def open_contracts_txt_file(folder_path, contract_file_name):
    contracts_file_path = os.path.join(folder_path,'contracts_dapp_' + contract_file_name+'.txt')
    if not os.path.isfile(contracts_file_path):
        print("The contract_txt file does not exist.")
        return None # falls die Datei nicht wichtiger wird. sonst sys.exit(1)
    
    with open(contracts_file_path, 'r') as file:
        contracts = file.read().splitlines()
        
    #print("Successfully read the contracts from the file")
    return contracts

def check_which_formatType_exists(file_path):
    # Check for CSV and PKL files
    if os.path.exists(f"{file_path}.csv"):
        format_type = ".csv"
    elif os.path.exists(f"{file_path}.pkl"):
        format_type = ".pkl"
    else:
        print(f"Error: The file {file_path} does not exist") 
        sys.exit(1) # Exits the script with a status code of 1 to indicate an error
    
    return format_type

def check_if_file_exists(file_path,format_type):
    # Check if the file exists
    if os.path.exists(os.path.join(file_path+format_type)):
        return file_path
    else:
        print(f"Error: The file {file_path+format_type} does not exist") 
        sys.exit(1) # Exits the script with a status code of 1 to indicate an error

def check_config_file():
    config_file_path = 'config.json'
    if not os.path.isfile(config_file_path):
        print("Config file does not exist.")
        sys.exit(1)

    # Load the config file
    with open(config_file_path, 'r') as file:
        config = json.load(file)

    # Check if the required keys exist in the config file
    required_keys = ["port", "protocol", "host", "input_folder_path", "input_contract_file_name"]
    for key in required_keys:
        if key not in config:
            print(f"Config file is missing the key: {key}")
            sys.exit(1)

    return config

def open_address_file(folder_path, contract_file_name):
    list_address_type_file_path = os.path.join(folder_path, 'list_address_type_'+contract_file_name+'.txt')
    if not os.path.isfile(list_address_type_file_path):
        print("The file list_address_type does not exist.")
        sys.exit(1)
    
    with open(list_address_type_file_path, 'r') as file:
        address_dict = {}
        for line in file:
                key, value = line.strip().split(':', 1)
                address_dict[key] = value
        
    print("Successfully read the list_address_type from the file")
    return address_dict

def save_preprocessed_file(df, file_path, format_type):
    # Save the preprocessed DataFrame to a new File

    # Construct the new file path based on the presence of the format_type in the original file path
    if format_type in file_path:
        preprocessed_path = file_path.replace(format_type, f'_preprocessed{format_type}')
    else:
        preprocessed_path = file_path + f'_preprocessed{format_type}'
    
    # Save the DataFrame to the appropriate file format
    if format_type == ".csv":
        df.to_csv(preprocessed_path, index=False)
    elif format_type == ".pkl":
        df.to_pickle(preprocessed_path)

def read_input_file(input_csv_file_path, format_type):
    # Read the CSV or pickle file into a pandas DataFrame
    if format_type == ".csv":
        df = pd.read_csv(input_csv_file_path+format_type, low_memory=False)
    elif format_type == ".pkl":
        df = pd.read_pickle(input_csv_file_path+format_type) #for pickle files
    else:
        raise ValueError("The input file format is not supported")
    
    return df

def get_contract_address_from_blockrange_name(file_name):
    # Extract the contract address from the file name
    contract_address = file_name.split('_')[0]
    return contract_address

def get_kind_of_Sc(sc_address, node_url, likehood_threshold):
    #check if the file already exists
    if os.path.exists(f"output/which_kind_of_Sc_{sc_address}.txt"):
        print("Reading file which kind of Smart Contract it is...", sc_address)  
        with open(f"output/which_kind_of_Sc_{sc_address}.txt", 'r') as file:
            which_token = int(file.read())

    else:
        print("Checking which kind of Smart Contract it is...", sc_address)
        which_token = ethereumnode.check_if_address_is_a_token(sc_address, node_url, likehood_threshold)
        # Save which token as a txt file
        with open(f"output/which_kind_of_Sc_{sc_address}.txt", 'w') as file:
            file.write(str(which_token))
    
    return which_token