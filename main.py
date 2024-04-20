import pm4py
import pandas as pd
import pm_discovery
import preprocess_and_convert_to_ocel

def main():
    # Path to your OCEL log file (JSON or XML format)
    input_csv_file_path = "/Users/tomfunke/Desktop/Detector/testset/df_call_dapp_with_ether_transfer_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000forsage.csv"
    #call_dapp forsage "/Users/tomfunke/Desktop/Detector/testset/df_call_dapp_with_ether_transfer_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000forsage.csv"
    #3 try mit kitty"/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x06012c8cf97bead5deae237070f9587f8e7a266d_4605167_4615167Kitty.csv"
    #2 try mit million "/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0xbcf935d206ca32929e1b887a07ed240f0d8ccd22_8447267_8458000million.csv"
    #1 try mit forsage'/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000Forsage.csv'
    #direct paths to test
    direct_path_to_example = '/Users/tomfunke/Desktop/Detector/testset/example_log.csv'
    direct_path_to_preprocessed = '/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000_preprocessed.csv'

    # Preprocess the CSV and get the OCEL object
    #events_ocel = preprocess_and_convert_to_ocel.convert_events_dapp_to_ocel(input_csv_file_path)
    call_dapp_ocel = preprocess_and_convert_to_ocel.convert_call_dapp_to_ocel(input_csv_file_path)

    # Discover the Object-Centric Petri Net (OC-PN) and Object-Centric Directly-Follows Graph (OC-DFG)
    pm_discovery.pn_and_dfg_discovery(call_dapp_ocel)

if __name__ == "__main__":
    main()
