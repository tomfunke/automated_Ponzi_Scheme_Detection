import pm4py
import os
import pandas as pd
import pm_discovery
import preprocess_and_convert_to_ocel
import sys
import helper

def main():
    """
    Input is
    (1)directory path, and a 
    (2)contract_address with their range as name, and the 
    (3)object selection
    """
    # Path to log folder
    input_file_path = "/Users/tomfunke/Desktop/logging/locale_extraktion/etherDoubler"
    #"/Users/tomfunke/Desktop/logging/locale_extraktion/forsage_120k_60k_ab_creation"
    #"/Users/tomfunke/Desktop/logging/locale_extraktion/millionmoney_200k"
    
    # Just the name without the prefix and suffix
    input_contract_file_name = "0xfd2487cc0e5dce97f08be1bc8ef1dce8d5988b4d_1014288_12679208"
    #"0x5acc84a3e955bdd76467d3348077d003f00ffb97_9315825_9454321"
    #"0xbcf935d206ca32929e1b887a07ed240f0d8ccd22_8447267_8654321"
    

    # Object selection
    # TODO: Noch zutreffend bei unterdschiedlichen files?
    object_selection = ["from"]

    """
    Pathing
    """   
    trace_tree_path = os.path.join(input_file_path,'df_trace_tree_' + input_contract_file_name)
    events_dapp__path = os.path.join(input_file_path,'df_events_dapp_' + input_contract_file_name)
    value_calls_dapp_path = os.path.join(input_file_path,'df_call_dapp_with_ether_transfer_' + input_contract_file_name)
    zero_value_calls_dapp_path = os.path.join(input_file_path,'df_call_dapp_with_no_ether_transfer_' + input_contract_file_name)
    delegatecall_dapp_path = os.path.join(input_file_path,'df_delegatecall_dapp_' + input_contract_file_name)
    format_type_trace_tree = helper.check_file_exists(trace_tree_path)
    
    """
    Here begins the main function
    """
    output = preprocess_and_convert_to_ocel.preprocess(format_type_trace_tree, trace_tree_path,events_dapp__path, value_calls_dapp_path, zero_value_calls_dapp_path, delegatecall_dapp_path)
    # Preprocess the CSV and get the OCEL object: https://pm4py.fit.fraunhofer.de/static/assets/api/2.7.8/pm4py.objects.ocel.html#pm4py.objects.ocel.obj.OCEL
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
