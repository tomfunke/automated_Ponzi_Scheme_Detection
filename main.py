import pm4py
import os
import pandas as pd
import pm_discovery
import preprocess_and_convert_to_ocel

def main():
    """
    Input is
    (1)Filepath and a 
    (2)boolean if the CSV is a call or event dapp and the 
    (3)object selection
    """
    # Path to your OCEL log file (JSON or XML format)
    input_file_path = "/Users/tomfunke/Desktop/Detector/testset/df_call_dapp_with_ether_transfer_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9315825_9454321forsage.pkl"
    #call_dapp forsage "/Users/tomfunke/Desktop/Detector/testset/df_call_dapp_with_ether_transfer_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000forsage.csv"
    #3 try mit kitty"/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x06012c8cf97bead5deae237070f9587f8e7a266d_4605167_4615167Kitty.csv"
    #2 try mit million "/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0xbcf935d206ca32929e1b887a07ed240f0d8ccd22_8447267_8458000million.csv"
    #1 try mit forsage'/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000Forsage.csv'
    #direct paths to test
    direct_path_to_example = '/Users/tomfunke/Desktop/Detector/testset/example_log.csv'
    direct_path_to_preprocessed = '/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000_preprocessed.csv'

    #Bool Input which kind of file: events_dapp == true or call_dapp == false
    is_events_dapp = False

    # Object selection
    object_selection = ["from"]

    """
    Slice name out of the path
    """
    # Slice the name out of the path
    filename = os.path.basename(input_file_path)
    filename_without_extension = os.path.splitext(filename)[0]
    format_type = os.path.splitext(filename)[1]


    """
    Here begins the main function
    """

    # Preprocess the CSV and get the OCEL object: https://pm4py.fit.fraunhofer.de/static/assets/api/2.7.8/pm4py.objects.ocel.html#pm4py.objects.ocel.obj.OCEL
    #chooses one of the functions based on the boolean based on the input file
    # select which coloumn is the object
    if is_events_dapp:
        ocel = preprocess_and_convert_to_ocel.convert_events_dapp_to_ocel(format_type, input_file_path, object_selection)
    else:
        ocel = preprocess_and_convert_to_ocel.convert_call_dapp_to_ocel(format_type, input_file_path, object_selection)

    # Discover the Object-Centric Petri Net (OC-PN) and Object-Centric Directly-Follows Graph (OC-DFG)
    #ocel is the input object
    #filename_without_extension is for saving the output
    pm_discovery.pn_and_dfg_discovery(ocel, filename_without_extension)
    

if __name__ == "__main__":
    main()
