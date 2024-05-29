import os
import pandas as pd
import pm_discovery
import preprocess_and_convert_to_ocel
import helper
import etherenode

def main():
    """
    Input is
    (1) set the path to the log folder,
    (2) set the name of the files without the prefix and suffix (main contract_address with range),
    (3) set the object selection (e.g., ["from", "to", "input", "output", "gas", "gasUsed", "functionName", "error", "calltype"])
    
    Please use only one format type (either CSV or PKL) for the input files. Not mixed.
    Input files are:
    (1) df_trace_tree
    (2) df_events_dapp
    (3) df_call_dapp_with_ether_transfer
    (4) df_call_dapp_with_no_ether_transfer
    (5) df_delegatecall_dapp
    (6) df_call_with_ether_transfer_non_dapp
    Even if the dataframes are empty, the files must exist. To ensure that no data has been neglected.


    Output is
    """
    # Path to log folder
    input_folder_path = "/Users/tomfunke/Desktop/logging/locale_extraktion/inklusive_nondapp/etheramid"
    #"/Users/tomfunke/Desktop/logging/locale_extraktion/etherDoubler"
    #"/Users/tomfunke/Desktop/logging/locale_extraktion/forsage_120k_60k_ab_creation"
    #"/Users/tomfunke/Desktop/logging/locale_extraktion/millionmoney_200k"
    
    # Just the name without the prefix and suffix (main contract_address with range)
    # example: "0x9758da9b4d001ed2d0df46d25069edf53750767a_1335983_1497934"
    input_contract_file_name = "0x9758da9b4d001ed2d0df46d25069edf53750767a_1335983_1497934"
    #"0xfd2487cc0e5dce97f08be1bc8ef1dce8d5988b4d_1014288_12679208"
    #"0x5acc84a3e955bdd76467d3348077d003f00ffb97_9315825_9454321"
    #"0xbcf935d206ca32929e1b887a07ed240f0d8ccd22_8447267_8654321"
    
    """
    your ethereum node configuration
    """
    port = 8547 #config["port"]
    protocol = "http://" #config["protocol"]
    host = "127.0.0.1" #config["host"]

    # ethereum node url
    node_url = protocol + host + ":" + str(port)


    # Object selection
    # TODO: Noch zutreffend bei unterdschiedlichen files?
    object_selection = ["from"]

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
    # was ist mit CREATIONS DAPP? enthält im "to" weitere contract addresses für objekte
    print("pathing done")

    """
    Here begins the main function
    """
    # Preprocess the CSV and get the OCEL object: https://pm4py.fit.fraunhofer.de/static/assets/api/2.7.8/pm4py.objects.ocel.html#pm4py.objects.ocel.obj.OCEL
    #output = preprocess_and_convert_to_ocel.preprocess(format_type_trace_tree, trace_tree_path,events_dapp__path, value_calls_dapp_path, zero_value_calls_dapp_path, delegatecall_dapp_path, value_calls_non_dapp_path, input_folder_path, input_contract_file_name)
    
    # test ethernode
    addresses = ["0x9758da9b4d001ed2d0df46d25069edf53750767a","0x176CA8f5676D5B916a5f65926124218C27a4c47A"]
    etherenode.Check_addresses_for_address_type(addresses, node_url)

    # legacy code: for each file own preprocess and ocel conversion
    #events_ocel = preprocess_and_convert_to_ocel.convert_events_dapp_to_ocel(format_type, input_file_path, object_selection)
    #Calls_ocel = preprocess_and_convert_to_ocel.convert_call_dapp_to_ocel(format_type, input_file_path, object_selection)
    """
    # Discover the Object-Centric Petri Net (OC-PN) and Object-Centric Directly-Follows Graph (OC-DFG)
    #ocel is the input object
    #filename_without_extension is for saving the output
    pm_discovery.pn_and_dfg_discovery(ocel, input_contract_address_with_range)
    """

if __name__ == "__main__":
    main()
