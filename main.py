import pm4py
import pandas as pd
import pm_discovery
import preprocess_and_convert_to_ocel

def main():
    # Path to your OCEL log file (JSON or XML format)
    input_csv_file_path = '/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000.csv'
    #direct paths to test
    direct_path_to_example = '/Users/tomfunke/Desktop/Detector/testset/example_log.csv'
    direct_path_to_preprocessed = '/Users/tomfunke/Desktop/Detector/testset/df_events_dapp_0x5acc84a3e955bdd76467d3348077d003f00ffb97_9391396_9393000_preprocessed.csv'

    # Preprocess the CSV and get the OCEL object
    ocel = preprocess_and_convert_to_ocel.convert_events_dapp_to_ocel(input_csv_file_path)

    # Discover the Object-Centric Petri Net (OC-PN) and Object-Centric Directly-Follows Graph (OC-DFG)
    pm_discovery.pn_and_dfg_discovery(ocel)

if __name__ == "__main__":
    main()
