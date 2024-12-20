import os
import pandas as pd
import pm_discovery
import preprocess_and_convert_to_ocel
import helper
import ponzi_criteria
import pm4py

def main():
    """
    Input is
    (1) set the path to the log folder,
    (2) set the name of the files without the prefix and suffix (main contract_address with range if range is part of name),
    (3) set the ethereum node configuration (host, port, protocol)
    Therefore use config file to set the path to the log folder and the name of the files and the ethereum node configuration!

    Please use only one format type (either CSV or PKL) for the input files. Not mixed.
    Input files are:
    (1) df_trace_tree
    (2) df_events_dapp
    (3) df_call_dapp_with_ether_transfer
    (4) df_call_dapp_with_no_ether_transfer
    (5) df_delegatecall_dapp
    (6) df_call_with_ether_transfer_non_dapp
    Even if the dataframes are empty, the files must exist. To ensure that no data has been neglected.

    Therefore you need to to set the correct configuration in the config file of the extraction tool (not in this script!):
        "extract_normal_transactions": true,
        "extract_internal_transactions": true,
        "extract_transactions_by_events": true,
        "dapp_decode_events": true,
        "dapp_decode_calls_with_ether_transfer": true,
        "dapp_decode_calls_with_no_ether_transfer": true, 
        "dapp_decode_delegatecalls": true,
        "non_dapp_decode_events": false,
        "non_dapp_decode_calls_with_ether_transfer": true,
        "non_dapp_decode_calls_with_no_ether_transfer": false, 
        "non_dapp_decode_delegatecalls": false

    Ensure you are connected to the Ethereum node and the node is running!


    Output is
    """
    print("Starting...")

    # Read the config file
    config = helper.check_config_file()
    
    # Extract the values from the config file
    port = config["port"]
    protocol = config["protocol"]
    host = config["host"]
    input_folder_path = config["input_folder_path"]
    input_contract_file_name = config["input_contract_file_name"]
    likelihood_threshold = config["likelihood_threshold"]

    
    # ethereum node url
    node_url = protocol + host + ":" + str(port)

    """
    Pathing
    """
    # Check if the files exists
    trace_tree_path = os.path.join(input_folder_path,'df_trace_tree_' + input_contract_file_name)
    format_type_trace_tree = helper.check_which_formatType_exists(trace_tree_path)
    events_dapp__path = helper.check_if_file_exists(os.path.join(input_folder_path,'df_events_dapp_' + input_contract_file_name),format_type_trace_tree)
    value_calls_dapp_path = helper.check_if_file_exists(os.path.join(input_folder_path,'df_call_dapp_with_ether_transfer_' + input_contract_file_name),format_type_trace_tree)
    zero_value_calls_dapp_path = helper.check_if_file_exists(os.path.join(input_folder_path,'df_call_dapp_with_no_ether_transfer_' + input_contract_file_name),format_type_trace_tree)
    delegatecall_dapp_path = helper.check_if_file_exists(os.path.join(input_folder_path,'df_delegatecall_dapp_' + input_contract_file_name),format_type_trace_tree)
    value_calls_non_dapp_path = helper.check_if_file_exists(os.path.join(input_folder_path,'df_call_with_ether_transfer_non_dapp_' + input_contract_file_name),format_type_trace_tree)
    

    #contracts_dapp_ .txt
    contracts_dapp_ = helper.open_contracts_txt_file(input_folder_path, input_contract_file_name)
    print(contracts_dapp_)
    print("pathing done")

    """
    Here begins the main function
    """
    # Preprocess the CSV and get the OCEL object: https://pm4py.fit.fraunhofer.de/static/assets/api/2.7.8/pm4py.objects.ocel.html#pm4py.objects.ocel.obj.OCEL
    ocel = preprocess_and_convert_to_ocel.preprocess(format_type_trace_tree, trace_tree_path,events_dapp__path, value_calls_dapp_path, zero_value_calls_dapp_path, delegatecall_dapp_path, value_calls_non_dapp_path, input_folder_path, input_contract_file_name, node_url)
    
    # legacy code: for each file own preprocess and ocel conversion
    #object_selection = ["from"]
    #events_ocel = preprocess_and_convert_to_ocel.convert_events_dapp_to_ocel(format_type, input_file_path, object_selection)
    #Calls_ocel = preprocess_and_convert_to_ocel.convert_call_dapp_to_ocel(format_type, input_file_path, object_selection)
    
    # Discover the Object-Centric Petri Net (OC-PN) and Object-Centric Directly-Follows Graph (OC-DFG)
    #ocel is the input object centric log
    #filename is for saving the output
    pm_discovery.pn_and_dfg_discovery(ocel, input_contract_file_name)

    #TODO Skip the preproccess by loading the ocel from the file
    #pd.options.mode.copy_on_write = True  # settingwithcopywarning-in-pandas
    #ocel = pm4py.read_ocel(os.path.join(input_folder_path, 'df_ocel_events_' + input_contract_file_name + '.csv'), os.path.join(input_folder_path, 'df_ocel_objects_' + input_contract_file_name + '.csv'))
    
    # Check the Ponzi criteria
    ponzi_criteria.check_ponzi_criteria(ocel, input_contract_file_name, input_folder_path, node_url, likelihood_threshold)

if __name__ == "__main__":
    main()
