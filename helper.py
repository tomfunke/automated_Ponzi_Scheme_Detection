import os
import sys
import json

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

