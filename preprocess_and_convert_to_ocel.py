import pm4py
import pandas as pd
import numpy as np
import os
import ethereumnode
import re
import helper

def convert_df_coloumns(df):
    # add a column "name" if it does not exist -> necessary for process mining
    if "name" not in df.columns.values.tolist():
        df["name"] = "" 

    # Rename the columns to match the OCEL standard
    df.rename(columns={"name": "concept:name"}, inplace=True)#concept:name is the activity
    df.rename(columns={"timeStamp": "time:timestamp"}, inplace=True)
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], dayfirst=False)

    # Remove unnecessary columns if present
        # functionName is a legacy column that is no longer used in the logger
    if "Unnamed: 0" in df.columns.values.tolist():
        df.drop(["Unnamed: 0"], inplace=True, axis=1)
    if "functionName" in df.columns.values.tolist():
        df.drop(["functionName"], inplace=True, axis=1)

    return df


def revert_txs(df):
    """
    Leagacy
    """
    # This error DataFrame includes only the columns "error" and "hash", which are essential for identifying errors associated with transaction hashes.
    errors = df[['error', 'hash']]
    errors.reset_index(inplace=True, drop=True)

    # Creates a boolean mask, mask_reverted, that identifies rows in the DataFrame where the "error" column contains specific error messages associated with transaction reversion. 
    mask_reverted = errors["error"].isin([
        'out of gas', 
        'invalid jump destination',
        'execution reverted',
        'write protection',
        'invalid opcode: INVALID',
        'contract creation code storage out of gas'
        ])
    # Uses this mask to extract the unique transaction hashes ("hash") associated with these errors, storing them in a set called txs_reverted
    txs_reverted = set(errors[mask_reverted]["hash"])
    
    # Create a mask for transactions that are NOT reverted
    mask_not_reverted = ~df["hash"].isin(list(txs_reverted))
    
    # Use the mask to filter the DataFrame, keeping only rows where the transaction hash is not in txs_reverted
    df = df[mask_not_reverted]

    return df

def convert_events_dapp_to_ocel(format_type, file_path, object_selection):
    #legacy
    df = helper.read_input_file(file_path, format_type)
    df = convert_df_coloumns(df)

    # Creates a list of all columns that are additional for the OCEL as event attributes: All Coloumns - the chosen object - the standard columns time and activity
    main_coloumns = np.array(['concept:name', 'time:timestamp']+object_selection)
    remaining_attributes = np.setdiff1d(df.columns.to_numpy(), main_coloumns)
    #example_objects = ["user"] # either choose objective via Input here or its always coloumn 9! (user/owner)
    #remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber"] + additional_columns
    
    #converts the dataframe to ocel format with the given object types: https://pm4py.fit.fraunhofer.de/static/assets/api/2.7.8/generated/pm4py.convert.convert_log_to_ocel.html
    ocel = pm4py.convert_log_to_ocel(df, object_types=object_selection, additional_event_attributes = remaining_attributes)

    helper.save_preprocessed_file(df, file_path, format_type)
    
    return ocel

def convert_call_dapp_to_ocel(format_type, file_path, object_selection):
    #legacy
    df = helper.read_input_file(file_path, format_type)
    # Remove rows where 'name' is None or ''
    # This is necessary because the OCEL importer does not accept empty activity names: so effectively, we are removing every Error like out of gas
    #df = df[df['name'].notna() & (df['name'] != '')]

    # Deletes all rows where their hash is acosiated with an error
    df = revert_txs(df)

    
    df = convert_df_coloumns(df)

    # Creates a list of all columns that are additional for the OCEL as event attributes: All Coloumns minus the chosen object minus the standard columns time and activity
    remaining_attributes = np.setdiff1d(df.columns.to_numpy(), np.array(['concept:name', 'time:timestamp']+object_selection))
    #object_selection = ["from"] # either choose objective via Input here or its always coloumn 2! "from"
    #remaining_attributes = ["address", "tracePos", "tracePosDepth", "hash", "blocknumber", "to", "callvalue", "input", "output", "gas", "gasUsed", "functionName", "error", "calltype"] # hier fehlen noch spalten
    
    #converts the dataframe to ocel format with the given object types
    #ocel = pm4py.convert_log_to_ocel(df, object_types=object_selection, additional_event_attributes = remaining_attributes)

    helper.save_preprocessed_file(df, file_path, format_type)
    
    #return ocel

def create_a_set_of_error_txs(df):
    # This error DataFrame includes only the columns "error" and "hash", which are essential for identifying errors associated with transaction hashes.
    errors = df[['error', 'hash']]
    errors.reset_index(inplace=True, drop=True)

    # Creates a boolean mask, mask_reverted, that identifies rows in the DataFrame where the "error" column contains specific error messages associated with transaction reversion. 
    mask_reverted = errors["error"].isin([
        'out of gas', 
        'invalid jump destination',
        'execution reverted',
        'write protection',
        'invalid opcode: INVALID',
        'contract creation code storage out of gas'
        ])
    # Uses this mask to extract the unique transaction hashes ("hash") associated with these errors, storing them in a set called txs_reverted
    txs_hashes = set(errors[mask_reverted]["hash"])

    return txs_hashes

def filter_txs_with_errors(df, txs_hashes):
    # Create a mask for transactions that are NOT reverted
    mask_not_reverted = ~df["hash"].isin(list(txs_hashes))
    
    # Use the mask to filter the DataFrame, keeping only rows where the transaction hash is not in txs_reverted
    df = df[mask_not_reverted]

    return df

def rename_activities_in_calls(value_calls_df):
    # empty values in the column "concept:name"
    mask = (value_calls_df["concept:name"].isna() | (value_calls_df["concept:name"] == "") ) & (value_calls_df["calltype"] == "CALL")
    value_calls_df.loc[mask, "concept:name"] = "call and transfer ether"
    
    return value_calls_df

def rename_activities_in_delegatecalls(delegatecall_df):
    # empty values in the column "concept:name"
    mask = (delegatecall_df["concept:name"].isna() | (delegatecall_df["concept:name"] == "") ) & (delegatecall_df["calltype"] == "DELEGATECALL")
    delegatecall_df.loc[mask, "concept:name"] = "delegate call and transfer Ether"
    return delegatecall_df

def rename_activities_in_events(events_df):
    # empty values in the column "concept:name"
    mask = (events_df["concept:name"].isna() | (events_df["concept:name"] == "") )
    events_df.loc[mask, "concept:name"] = "undecoded event"
    return events_df


def get_address_types(addresses, node_url, folder_path, contract_file_name):
    """
    This function checks if the addresses are smart contracts or externally owned accounts (EOAs)
    and returns a dictionary with the address as the key and the address type as the value.
    If the file list_address_type.txt exists, the function reads the file instead of connecting to the node.
    If the file does not exist, the function connects to the Ethereum node to check the address types.
    """
    list_address_type_file_path = os.path.join(folder_path, 'list_address_type_'+contract_file_name+'.txt')

    if os.path.exists(list_address_type_file_path):
    # if file exists read file instead of connecting to the node
        with open(list_address_type_file_path, 'r') as file:
            address_dict = {}
            for line in file:
                key, value = line.strip().split(':', 1)
                address_dict[key] = value
        
        print("Successfully read the list_address_type from the file")
        return address_dict
    
    else:
    # if file does not exist connect to the node    
        # check if the addresses are smart contracts or externally owned accounts (EOAs) by connecting to the Ethereum node
        set_of_addresses = set(addresses) # create a set of unique addresses for faster processing
        #print(set_of_addresses)
        address_dict = ethereumnode.check_addresses_for_address_type(set_of_addresses, node_url)
        print("Successfully checked the address types with the Ethereum node")

        # Save list_address_type as a file on your device for future use
        with open(list_address_type_file_path, 'w') as file:
            for key, value in address_dict.items():
                file.write(f"{key}:{value}\n")

        print("Successfully saved the list_address_type to a file")
        return address_dict

def preprocess(format_type, trace_tree_path, events_dapp_path, value_calls_dapp_path, zero_value_calls_dapp_path, delegatecall_dapp_path, value_calls_non_dapp_path, folder_path, contract_file_name, node_url):
    """
    Filters errors & converts tables & saves them in a new file

    Args:
        trace_tree_path (path): 
        dict_abi (dict): 

    Raises:
        ValueError: 

    Returns:
        pd.DataFrame: A DataFrame with 

    Overview:
        The function first 
    """
    ##### TRACE TREE #####
    # just for finding the error txs
    # Read the input tracetree file
    tracetree = helper.read_input_file(trace_tree_path, format_type)
    
    # create a set of all transactions that are associated with an error
    set_of_txs_to_revert = create_a_set_of_error_txs(tracetree)
    
    # memory management
    del tracetree

    #### PREPROCESSING ####
    #Create a list of tuples, each tuple containing the path and name of the file
    # This is done to avoid code duplication
    dapp_list = [(events_dapp_path, "EVENTS DAPP"),
                 (value_calls_dapp_path, "VALUE CALLS"), 
                 (zero_value_calls_dapp_path, "ZERO VALUE CALLS"), 
                 (delegatecall_dapp_path, "DELEGATECALL"),
                 (value_calls_non_dapp_path, "VALUE CALLS NON DAPP")
                 ]
    # Dictionary to hold each DataFrame
    dataframes = {}

    # Iterate over each file to preprocess
    for dapp_path, dapp_name in dapp_list:
        dapp_df = helper.read_input_file(dapp_path, format_type)

        # Check if the DataFrame is empty or contains only zero values
        if dapp_df.empty or (dapp_df == 0).all().all():
            #print(f"Skipping {dapp_name} processing as the DataFrame is empty or contains only zero values.")
            # flag dataframe as empty/ None
            dataframes[dapp_name] = None
            
        else:
            #### Actual Preprocessing here ####
            dapp_df = filter_txs_with_errors(dapp_df, set_of_txs_to_revert)
            dapp_df = convert_df_coloumns(dapp_df)

            # Rename activities in Calls (every file except EVENTS DAPP)
            if dapp_name != "EVENTS DAPP" and dapp_name != "DELEGATECALL":
                dapp_df = rename_activities_in_calls(dapp_df)

            if dapp_name == "DELEGATECALL":    
                dapp_df = rename_activities_in_delegatecalls(dapp_df)
            
            # preprocess only EVENTS dapp
            if dapp_name == "EVENTS DAPP":
                # convert the address to lowercase: in a old version of the extractor the address was not converted to lowercase
                dapp_df["address"] = dapp_df["address"].str.lower()

                # Datacleaning for from and to column if there are events with special attributes
                # Check if the "to" column exists before applying the replacement because not all Dapps have the "to" column
                # example https://etherscan.io/tx/0x4b0a9a2956a103e0fbcda0b21dbdac046cb6fd09ddd792db760873334898e660#eventlog
                if "to" in dapp_df.columns:
                    # delete the decimal numbers in the to-address, but only if not NaN and string. 
                    dapp_df["to"] = dapp_df["to"].apply(lambda x: re.sub(r'^\d+$', '', x) if pd.notna(x) and isinstance(x, str) else x)
                if "from" in dapp_df.columns:
                    # delete the decimal numbers in the from-address, but only if not NaN and string. 
                    dapp_df["from"] = dapp_df["from"].apply(lambda x: re.sub(r'^\d+$', '', x) if pd.notna(x) and isinstance(x, str) else x)

                # Rename activities in Events Dapp
                dapp_df = rename_activities_in_events(dapp_df)

            helper.save_preprocessed_file(dapp_df, dapp_path, format_type)

            #store each DataFrame with a specific variable name dynamically after processing, for further data handling
            dataframes[dapp_name] = dapp_df
    
    print("preprocessed each file. Now combining...")    
    
    # combines all dataframes in the dictionary dataframes if they are not None /empty
    combined_df = pd.concat([df for df in dataframes.values() if df is not None])
    combined_df = combined_df.reset_index(drop=True) # reset the index, which will assign a new, unique index to each row
    
    # Convert the column to numeric, coercing errors to NaN (if any non-numeric values)
    combined_df['callvalue'] = pd.to_numeric(combined_df['callvalue'], errors='coerce')


    # sort by timestamp (timestamp of the block), transaction index (order in block) and trace position (order in transaction)
    # blocknumber vernachlässigen, da timestamp gleiche ist?
    # timestamp und transactionIndex sind nicht unique, da eine Transaktion mehrere Events haben kann -> nutze daher tracePos! in kombination mit den anderen beiden
    # TODO: implement tracePosDepth statt tracePos für Baumstruktur -> furter research
    combined_df = combined_df.sort_values(["time:timestamp", "transactionIndex", "tracePos"])
    
    # checks if the column "address" exists in the dataframe
    if "address" in combined_df.columns:
        # combine the "address" and "to" columns into a new column "Address_o" (object)
        combined_df["Address_o"] = combined_df["address"].combine_first(combined_df["to"]) # erste implementiert war andersrum: combined_df["to"].combine_first(combined_df["address"])
        #just for checking the step: #helper.save_preprocessed_file(combined_df, os.path.join(folder_path,'df_combinded_' + contract_file_name), format_type)
    else:
        # if there is no "address" column, use the "to" column as the "Address_o" column
        combined_df["Address_o"] = combined_df["to"]
    
    # get the address types for the addresses of both coloumns, excluding NaN values
    address_set = set(combined_df["Address_o"].dropna()).union(set(combined_df["from"].dropna()))
    address_type_map = get_address_types(address_set, node_url, folder_path, contract_file_name)

    # adds a coloumn address_types to determine if the address(include to addresses) is a smart contract or an externally owned account (EOA)
    # map the address to the address type from the dictionary
    combined_df["Address_Type"] = combined_df["Address_o"].map(address_type_map) 

    # adds a coloumn from_Type to determine if the from-address is a smart contract or an externally owned account (EOA)
    #address_type_map = get_address_types(combined_df["from"], node_url, folder_path, contract_file_name)
    combined_df["from_Type"] = combined_df["from"].map(address_type_map)
    
    # from-object
    combined_df["from_o"] = combined_df["from"]

    helper.save_preprocessed_file(combined_df, os.path.join(folder_path,'df_combinded_' + contract_file_name), format_type)
    print("preprocess done")

    """
    OCEL

    converts the dataframe to ocel format with the given object types
    object_types is a list of strings that represent the columns in the dataframe that should be used as objects -> just the name of the coloumns
    """
    print("ocel converting...")

    object_selection = ["Address_o","from_o"] # ,"Address_Type", "from_Type" # types are additional attributes to differentiate between smart contracts and externally owned accounts (EOAs)
    object_attributes = {"Address_o": "Address_Type",
                         "from_o": "from_Type"
                         }

    # Creates a list of all columns that are additional for the OCEL as event attributes: All Coloumns - the chosen object - the standard columns time and activity
    main_coloumns = np.array(['concept:name', 'time:timestamp']+object_selection)
    remaining_attributes = np.setdiff1d(combined_df.columns.to_numpy(), main_coloumns) # remaining = all - main

    #actual Ocel converting
    # https://processintelligence.solutions/static/api/2.7.11/pm4py.html#pm4py.convert.convert_log_to_ocel
    ocel = pm4py.convert_log_to_ocel(combined_df, object_types = object_selection, additional_object_attributes = object_attributes, additional_event_attributes = remaining_attributes)
    #ocel = pm4py.convert_log_to_ocel(combined_df, object_types = object_selection, additional_event_attributes = remaining_attributes)
    
    # Save the OCEL events and object to a file
    pm4py.write_ocel_csv(ocel, os.path.join(folder_path,'df_ocel_events_' + contract_file_name + ".csv"),os.path.join(folder_path,'df_ocel_objects_' + contract_file_name + ".csv"))
    
    print("ocel converting done")
    return ocel
