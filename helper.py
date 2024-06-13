import os
import sys

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

