import pm4py
import pandas as pd
from datetime import datetime
from pm4py.objects.bpmn.importer import importer as bpmn_importer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.objects.conversion.bpmn import converter as bpmn_converter
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from collections import defaultdict, Counter
from pm4py.objects.ocel.util import flattening as ocel_flattening
import helper
import ethereumnode
from pandas import Timestamp
import numpy as np
import re
import matplotlib.pyplot as plt


def load_bpmn_petri(filename_without_extension):
    """
    bpmn to petri net
    returns the petri net
    """

    # Load the BPMN file
    bpmn_graph = bpmn_importer.apply("input/ponzi_actual.bpmn")
    
    # Visualize the imported BPMN
    gviz = bpmn_visualizer.apply(bpmn_graph)
    #bpmn_visualizer.view(gviz)

    # Convert BPMN to Petri net 
    net, initial_marking, final_marking = bpmn_converter.apply(bpmn_graph)
    print("net:", net)
    print("initial_marking:",initial_marking)
    print("final_marking:",final_marking)
    print("Places in the net:", net.places)
    print("Transitions in the net:", net.transitions)

    # Generate the visualization of the Petri net
    gviz = pn_visualizer.apply(net, initial_marking, final_marking)

    # Display the visualization (this will open in a new window)
    #pn_visualizer.view(gviz)

    # Save as PNG
    pn_visualizer.save(gviz, f'output/petri_net_visualization_{filename_without_extension}.png')
    
    # Save the Petri net in PNML format
    pnml_exporter.apply(net, initial_marking, f'output/saved_petri_net_{filename_without_extension}.pnml')

    return net, initial_marking, final_marking

def alignments_calculations(ocel):
    """"
     Using our own BPMN as reference model
     https://processintelligence.solutions/static/api/2.7.11/api.html#conformance-checking-pm4py-conformance
     # does not work with our log since they mostly have the same activity name: "call and transfer"
    """
    # Load the BPMN file and convert it to a Petri net
    net, initial_marking, final_marking = load_bpmn_petri("standard_ponzi")

    # transform the ocel to a XES log
    traditional_log = ocel_flattening.flatten(ocel, "ocel:type:Address_o") # gegebenenfalls noch from_o addresse als objekt
    print(traditional_log)

    #replayed_traces = pm4py.conformance_diagnostics_token_based_replay(traditional_log, net, initial_marking, final_marking)
    #print(replayed_traces)

    alignments_precision = pm4py.conformance.precision_alignments(traditional_log, net, initial_marking, final_marking)
    print(alignments_precision)

    alignments_fitness = pm4py.conformance.fitness_alignments(traditional_log, net, initial_marking, final_marking)
    print(alignments_fitness)

    return  alignments_precision,alignments_fitness

def plotting_tx(timestamps_unprofit, losses, profits_profitable_with_timestamp, timestamps_profit, profits_even_profit, timestamps_even_profit, profits_profit_no_timestamp, timestamps_profit_no_timestamp, filename_without_extension, which_timestamp):


    # Create scatter plot
    plt.figure(figsize=(10, 6))

    if timestamps_unprofit:
        plt.scatter(timestamps_unprofit, losses, color='red', label='Unprofitable Users')

    # Plot profitable users in blue
    if timestamps_profit:
        plt.scatter(timestamps_profit, profits_profitable_with_timestamp, color='green', label='Profitable Users')

    # Plot even profit users in green
    if timestamps_even_profit:
        plt.scatter(timestamps_even_profit, profits_even_profit, color='orange', label='Break-Even Users')

    # Plot profitable users with no original timestamp in orange
    if timestamps_profit_no_timestamp and profits_profit_no_timestamp:
        plt.scatter(timestamps_profit_no_timestamp, profits_profit_no_timestamp, color='blue', label='Non-Investing Profiteers')


    # Add labels and title
    plt.xlabel(f"Timestamp of First {which_timestamp}")
    plt.ylabel('Profit in Wei')
    plt.title(f"Profit distribution of the smart contract \n {filename_without_extension}")

    #Automatically Adjusting the X-Axis Limits
    #plt.xlim([min(timestamps_unprofit + timestamps_profit), max(timestamps_unprofit + timestamps_profit)])

    # Set the x-axis limits manually
    #plt.xlim(pd.Timestamp('2016-02-16'), pd.Timestamp('2016-08-16')) # ether_doubler_without_deployer has outlier in 2018
    #plt.xlim(pd.Timestamp('2016-02-16'), pd.Timestamp('2016-04-16')) # ether doubler noch mehr weg gecuttet um so sehen
    #plt.xlim(pd.Timestamp('2015-07-01'), pd.Timestamp('2016-07-01')) # ethereumpyrmadi has outlier in 
    #plt.xlim(pd.Timestamp('2016-01-01'), pd.Timestamp('2016-07-01')) # dynaumpyrmadi has outlier in 
    #plt.xlim(pd.Timestamp('2016-03-22'), pd.Timestamp('2016-03-29')) # piggy has outlier in 
    
    # Set the y-axis limits manually
    #plt.ylim([-0.2e19, 0.8e19]) #y-axe limit because millionmoney has this one huge outlier with 18 eth

    # Format x-axis for better date readability
    plt.gcf().autofmt_xdate()

    # Show legend and grid
    plt.legend()
    plt.grid(True)


    # Save the plot to a file
    plt.savefig(f"output/users_profits_vs_{which_timestamp}_{filename_without_extension}.png")

    # Display plot
    #plt.show()

    # Close the plot
    plt.close()

    return

def input_output_flow(ocel, filename_without_extension, folder_path, node_url, likehood_threshold):
    # Step 1: Extract relevant events and attributes
    events = ocel.events
    objects = ocel.objects
    
    # Step 2: 

    # first row
    first_row = events.iloc[0]
    #deployment_address = 
    first_caller= first_row["from"]
    first_input = first_row["input"]
    first_user = []
    address_dict = helper.open_address_file(folder_path, filename_without_extension)
    #"Traffic Light" for detection of Ponzi schemes
    scam_signal = {"R1": None,
                   "R2": None,
                   "R3": None,
                   "R4": None,
                   "A_percentage_of_profitable_users": None,
                   "A_median_profit": None,
                   "A_invested_amounts_frequency": None,
                   "P_directly_send_to_others": None,
                   "P_is_ether_transfer_heavy": None,
                   "P_is_often_send_to_previous_user": None,
                   "P_is_often_send_to_the_first_user": None,
                   "zero_tx_used_to_pay_out": None,
                   "zero_tx_used_to_payout_first_user": None,
                   "P_most_of_zero_tx_are_from_first_user": None,
                   "P_withdrawal_function_just_from_first_user": None
                   }


    # Regular expression pattern for Ethereum address
    address_pattern = r"^(0x)?[0-9a-fA-F]{40}$"

    #TODO check inputs with arrays...
    # Check if input matches the pattern and is therefore an ethereum address
    if isinstance(first_input, str) and re.match(address_pattern, first_input) and first_input != "0x" :
        print("Input is a valid Ethereum address")
        # check if input address is in the address_dict
        if first_input in address_dict:
            print("Input address is in the address_dict")
            first_user.append(first_input)
    else:
        print("Input is not a valid Ethereum address")
    first_user.append(first_caller)

    print("first users",first_user)
    #print(address_dict["0xfffc07f1b5f1d6bd365aa1dbc9d16b1777f406a2"])# if eoa or sc

    # get important timestamps of the events
    last_timestamp = events["ocel:timestamp"].max()
    print("Last timestamp:", last_timestamp)
    earliest_timestamp = events["ocel:timestamp"].min()

    # get the SC address
    sc_input = helper.get_contract_address_from_blockrange_name(filename_without_extension)

    # Step 3: Process the data
    address_balance = defaultdict(lambda: {"received": 0.0, "invested": 0.0, "first_transaction": None, "interaction_as_sender": 0, "interaction_as_receiver": 0, "first_interaction_as_sender": None})

    def update_balance(from_addr, to_addr, value):
        value = float(value)
        if from_addr:
            address_balance[from_addr]["invested"] += value
            address_balance[from_addr]["interaction_as_sender"] += 1
        if to_addr:
            address_balance[to_addr]["received"] += value
            address_balance[to_addr]["interaction_as_receiver"] += 1

    # count the different paths of the transactions
    counts = {"count_initial_paths": None, "count_zero_sending_paths": None}
    counts["count_initial_paths"] = {"initial_investment_to_Sc_by_EOA": 0,
                    "Sc_sends_to_another_user_in_same_transaction": 0,
                    "Sc_sends_to_multiple_users_in_same_transaction": 0,
                    "SC_does_not_send_to_others_in_same_transaction": 0,
                    "Internal_Upgrade_Event": 0,
                    "sc_sends_to_iniating_user" : 0,
                    "sc_sends_to_first_user" : 0,
                    "first_user_triggers_to_pay_out" : 0,
                    "counter_sending_to_previous_user" : 0
                   }
    counts["count_zero_sending_paths"] = {"sends_zero_to_SC": 0,  "joins_without_investing": 0,
                    "Sc_sends_to_another_user_in_same_transaction": 0,
                    "Sc_sends_to_multiple_users_in_same_transaction": 0,
                    "SC_does_not_send_to_others_in_same_transaction": 0,
                    "Internal_Upgrade_Event": 0,
                    "sc_sends_to_iniating_user" : 0,
                    "sc_sends_to_first_user" : 0,
                    "first_user_triggers_to_pay_out" : 0,
                    "counter_sending_to_previous_user" : 0
                    }
    counts["counter_user_sends_again_paths"] = {"invests_again": 0,
                    "Sc_sends_to_another_user_in_same_transaction": 0,
                    "Sc_sends_to_multiple_users_in_same_transaction": 0,
                    "SC_does_not_send_to_others_in_same_transaction": 0,
                    "Internal_Upgrade_Event": 0,
                    "sc_sends_to_iniating_user" : 0,
                    "sc_sends_to_first_user" : 0,
                    "first_user_triggers_to_pay_out" : 0,
                    "counter_sending_to_previous_user" : 0
                    }
    
    def innerloop_for_same_tx_hash(i, events, hash_of_this_tx, pathing_type, previous_user_id):
        # now check if same transaction has multiple transaction traces (tracePos)
        hash_of_this_tx = row["hash"]
        memory_of_this_hash = {"counter_how_often_sc_sends_to_others": 0,
                            "counter_how_often_internal_upgrade_event": 0,
                            "counter_how_often_sc_sends_to_iniating_user": 0,
                            "counter_how_often_sc_sends_to_first_user": 0,
                            "counter_how_often_sc_triggered_by_first_user_to_send_to_him": 0,
                            }
        # Inner loop: Start from the current position of the outer loop and stop when hash changes. Instead of iterating through all transactions again, the inner loop starts from the current index (i) of the outer loop and iterates forward until it encounters a different hash.
        for j in range(i, len(events)):
            inner_row = events.iloc[j]
            if inner_row["hash"] != hash_of_this_tx:
                #events.iloc[j-1]# in some transactions its just this one step and nothing more happens; j-i is the original line before we break in thi j
                
                # Save memory stats before breaking inner loop
                # this does not give the number of internal events and how many times the SC sends to others in the same transaction. It just counts plus 1 for each kind of trace
                if memory_of_this_hash["counter_how_often_sc_sends_to_others"] == 0: #  means that the SC does not send to another user in the same transaction-> kann ich das benutzen als path ende?
                    counts[pathing_type]["SC_does_not_send_to_others_in_same_transaction"] += 1
            
                if memory_of_this_hash["counter_how_often_sc_sends_to_others"] == 1:
                    counts[pathing_type]["Sc_sends_to_another_user_in_same_transaction"] += 1
                
                if memory_of_this_hash["counter_how_often_sc_sends_to_others"] > 1:
                    counts[pathing_type]["Sc_sends_to_multiple_users_in_same_transaction"] += 1 

                if memory_of_this_hash["counter_how_often_internal_upgrade_event"] > 0:
                    counts[pathing_type]["Internal_Upgrade_Event"] += 1
                
                if memory_of_this_hash["counter_how_often_sc_sends_to_iniating_user"] > 0:
                    counts[pathing_type]["sc_sends_to_iniating_user"] += 1
                
                if memory_of_this_hash["counter_how_often_sc_sends_to_first_user"] > 0:
                    counts[pathing_type]["sc_sends_to_first_user"] += 1

                if memory_of_this_hash["counter_how_often_sc_triggered_by_first_user_to_send_to_him"] > 0:
                    counts[pathing_type]["first_user_triggers_to_pay_out"] += 1
                
                break  # Stop inner loop when the hash changes 

            # Process the transactions with the same hash with multiple tracePos
            ####print(f"Processing transaction with the same hash: {inner_row['hash']} in trace Pos: {inner_row['tracePos']}")
            if inner_row["callvalue"] > 0:
                #user is the one who called the SC (the actual tx)

                # save the first receiver of the first sc sending
                if previous_user_id == None and inner_row["from"] == sc_input:
                    first_receiver = inner_row["to"]
                    print(" added first receiver(SC or EOA) as first user", first_receiver)
                    first_user.append(first_receiver)
                


                # check if the SC sends to another user
                if inner_row["from"] == sc_input and inner_row["to"] != user:
                    ####print("SC sends to another user in the same transaction")
                    memory_of_this_hash["counter_how_often_sc_sends_to_others"] += 1
                
                # check if the SC sends to the user who initiated the transaction (cash out)
                if inner_row["from"] == sc_input and inner_row["to"] == user:
                    ####print("SC sends to to the user who initiated the transaction")
                    memory_of_this_hash["counter_how_often_sc_sends_to_iniating_user"] += 1
                
                # check if the SC sends to the first user
                if inner_row["from"] == sc_input and inner_row["to"] in first_user:
                    ####print("SC sends to the first user")
                    memory_of_this_hash["counter_how_often_sc_sends_to_first_user"] += 1
                
                #first user triggers to pay out his share
                if inner_row["from"] == sc_input and user in first_user and inner_row["to"] in first_user :
                    ###print("first user is the one who calls the sc to pay him out")
                    memory_of_this_hash["counter_how_often_sc_triggered_by_first_user_to_send_to_him"] += 1
                
                # chain check?
                # if there is a previous_user_id and the receiver is the previous and its not the first line of tx where the SC is the receiver
                if previous_user_id != None and inner_row["to"] == previous_user_id and inner_row["to"] != sc_input:
                    counts[pathing_type]["counter_sending_to_previous_user"] += 1
                
            
            # check if events
            if "address" in inner_row:
                if inner_row["address"] == sc_input:
                    ####print("Internal Upgrade Event")
                    memory_of_this_hash["counter_how_often_internal_upgrade_event"] += 1
        
        return
    
    ####Main loop
    previous_user_id = None
    # iterate through the events
    for i, row in events.iterrows():
        user = row["from"]
        timestamp = row["ocel:timestamp"]

        if row["callvalue"] > 0:
            update_balance(row["from"], row["to"], row["callvalue"]) # Update the balance for the sender and receiver interacting with the contract

            # Check the timestamp of the first investment for each user = first transaction as sender (from)
            if address_balance[user]["first_transaction"] == None:
                address_balance[user]["first_transaction"] = timestamp
                
                # this means its the initial investment of a user to the Dapp (user A initiates transaction)
                # check if from_Typ is a contract or an EOA
                if(row["from_Type"] == "EOA"): # so it cant be the Dapps first sending transaction
                    ####print("Sender is a EOA: ", user)
                    #combined_df.loc[i+1, "concept:name"] = "user A initiates Transaction"-> idea to manipulate the events-> see branch
                    counts["count_initial_paths"]["initial_investment_to_Sc_by_EOA"] += 1

                    innerloop_for_same_tx_hash(i, events, row["hash"], "count_initial_paths", previous_user_id)
                    # Update previous_user_id for the next iteration
                    previous_user_id = user
                #else: row["from_Type"] == "SC" other sc which sending to the main SC on this path for their first time
            
            
            # Not first transaction of the user
            elif address_balance[user]["first_transaction"] != None:
                if (row["from_Type"] == "EOA"):
                    # its an EOA
                    ###print("investor is multiple times investing: ", user)
                    counts["counter_user_sends_again_paths"]["invests_again"] += 1
                    # TODO was passiert wenn ein user mehrmals investiert? -> wie wird das in der Abfgole berücksichtigt?
                    innerloop_for_same_tx_hash(i, events, row["hash"], "counter_user_sends_again_paths",previous_user_id)
                    previous_user_id = user
                #else: row["from_Type"] == "SC" other sc which sending again to the main SC on this path
        
        else: # no value in this transaction
            # events would be counted here because of no value in the transaction but therefore we check the "to" == sc_input next

            # if callvalue is 0 and someone is sending to the MAIN SC means its a trigger from outside the SC
            if(row["to"] == sc_input):
                ##print(user, " triggers from outside the SC")

                # joining without investing
                # first interaction and event happens but not value is sent
                if address_balance[user]["first_interaction_as_sender"] == None:
                    counts["count_zero_sending_paths"]["joins_without_investing"] += 1
                
                # add timestamp for first interaction as sender
                if address_balance[user]["first_interaction_as_sender"] == None:
                    address_balance[user]["first_interaction_as_sender"] = timestamp # now he joined
                    ##print("First interaction of user: ", user)
                
                # path of no value transactions
                counts["count_zero_sending_paths"]["sends_zero_to_SC"] += 1

                # Does SC got triggered to send?
                # if the SC sends to another user like in 0xa068bdda7b9f597e8a2eb874285ab6b864836cb8e48a1b6fccb0150bf44f5592 #coinbase ODER 0xa068bdda7b9f597e8a2eb874285ab6b864836cb8e48a1b6fccb0150bf44f5592 chicken
                # same hash should have callvalue > 0 and from = SC and to = user
                innerloop_for_same_tx_hash(i, events, row["hash"], "count_zero_sending_paths", previous_user_id)
                #previous_user_id = user
                
                
    # print initial_investment_to_Sc_by_EOA
    print(counts["count_initial_paths"])
    # bedeuted es jetzt bei coinbase {'initial_investment_to_Sc_by_EOA': 156, 'Sc_sends_to_another_user_in_same_transaction': 0, 'Sc_sends_to_multiple_users_in_same_transaction': 0, 'SC_does_not_send_to_others_in_same_transaction': 156, 'Internal_Upgrade_Event': 0}
    # wenn alles 0 ist, dass es kein Ponzi ist? die Überweisung endet halt nur vor erst hier. Kann ja durch 0 callvalue noch getriggert werden
    
    print(counts["count_zero_sending_paths"])

    print(counts["counter_user_sends_again_paths"])

    print("first users after loop",first_user)
    # Step 4: Calculate the ratios
    ###Ratios
    
    #Ratio of directly send to others
    ratio_initial_not_send_all = counts["count_initial_paths"]["SC_does_not_send_to_others_in_same_transaction"] / counts["count_initial_paths"]["initial_investment_to_Sc_by_EOA"]
    print("Initial investment: not directly sent to others ",ratio_initial_not_send_all)

    ratio_initial_between_directly_and_all = 1 - ratio_initial_not_send_all
    print("Initial investment: directly sent to others ",ratio_initial_between_directly_and_all)
    
    if ratio_initial_between_directly_and_all < 0.5:
        print("Ratio of directly send to others is less than 50%") # probably not ponzi
        scam_signal["P_directly_send_to_others"] = "Green"
    elif ratio_initial_between_directly_and_all > 0.8:
        print("Ratio of directly send to others is higher than 80%: maybe ponzi") # looks like ponzi structure because send directly to others
        scam_signal["P_directly_send_to_others"] = "Red"
    else:
        print("Ratio of directly send to others between 50 and 80%")
        scam_signal["P_directly_send_to_others"] = "Orange"

    # Ratio of: all tx with ether send to the SC from EOA / all tx to the SC from EOA (also 0 value tx)
    ratio_tx_with_eth_and_all_tx = (counts["count_initial_paths"]["initial_investment_to_Sc_by_EOA"] + counts["counter_user_sends_again_paths"]["invests_again"]) / (counts["count_initial_paths"]["initial_investment_to_Sc_by_EOA"] + counts["counter_user_sends_again_paths"]["invests_again"] + counts["count_zero_sending_paths"]["sends_zero_to_SC"])
    print("ratio_tx_with_eth_and_all_tx", ratio_tx_with_eth_and_all_tx)
    # if this is 1 it means that all transactions to the SC are with value -> sound like a Ponzi
    #only values?
    if ratio_tx_with_eth_and_all_tx == 1:
        print("All transactions to the SC are with value: probably Ponzi")
        scam_signal["P_is_ether_transfer_heavy"] = "Red"
    elif ratio_tx_with_eth_and_all_tx > 0.8:
        print("More than 80% of all transactions to the SC are with value: probably Ponzi")
        scam_signal["P_is_ether_transfer_heavy"] = "Red"
    elif ratio_tx_with_eth_and_all_tx > 0.5:
        print("More than 50% of all transactions to the SC are with value: maybe Ponzi")
        scam_signal["P_is_ether_transfer_heavy"] = "Orange"
    else: 
        print("Less than 50% of all transactions to the SC are with value")
        scam_signal["P_is_ether_transfer_heavy"] = "Green"

    # ratio counter_sending_to_previous_user
    ratio_tx_send_to_previous_and_all_value_tx = (counts["count_initial_paths"]["counter_sending_to_previous_user"] + counts["counter_user_sends_again_paths"]["counter_sending_to_previous_user"]) / (counts["count_initial_paths"]["initial_investment_to_Sc_by_EOA"] + counts["counter_user_sends_again_paths"]["invests_again"])
    print("ratio_tx_send_to_previous_and_all_value_tx ", ratio_tx_send_to_previous_and_all_value_tx)
    if ratio_tx_send_to_previous_and_all_value_tx > 0.5:
        print("More than 50% of all transactions are sending to the previous user") # probably chain
        scam_signal["P_is_often_send_to_previous_user"] = "Red"
    elif ratio_tx_send_to_previous_and_all_value_tx > 0.2 and ratio_tx_send_to_previous_and_all_value_tx <= 0.5:
        print("More than 20% and less than 50% of all transactions are sending to the previous user")
        scam_signal["P_is_often_send_to_previous_user"] = "Orange"
    else:
        print("Less than 20% of all transactions are sending to the previous user") # just no chain but maybe tree?
        scam_signal["P_is_often_send_to_previous_user"] = "Green"

    # ratio to first user counts["count_initial_paths"]["sc_sends_to_first_user"]
    ratio_tx_send_to_first_user_and_all_value_tx = (counts["count_initial_paths"]["sc_sends_to_first_user"] + counts["counter_user_sends_again_paths"]["sc_sends_to_first_user"]) / (counts["count_initial_paths"]["initial_investment_to_Sc_by_EOA"] + counts["counter_user_sends_again_paths"]["invests_again"])
    print("ratio_tx_send_to_first_user_and_all_value_tx ", ratio_tx_send_to_first_user_and_all_value_tx)
    if ratio_tx_send_to_first_user_and_all_value_tx > 0.2:
        print("More than 20% of all transactions are sending to the first user") # probably ponzi
        scam_signal["P_is_often_send_to_the_first_user"] = "Red"
    elif ratio_tx_send_to_first_user_and_all_value_tx > 0.1 and ratio_tx_send_to_first_user_and_all_value_tx <= 0.2:
        print("More than 10% and less than 20% of all transactions are sending to the first user") # maybe ponzi orange, or just fee for developer
        scam_signal["P_is_often_send_to_the_first_user"] = "Orange"
    else:
        print("Less than 10% of all transactions are sending to the first user") # just no initial user share. but could still be ponzi
        scam_signal["P_is_often_send_to_the_first_user"] = "Green"



    # sending zero path: counts["count_zero_sending_paths"]
    # etherdoubler sends back by triggering via  sends_zero_to_SC'
    if counts["count_zero_sending_paths"]["sc_sends_to_iniating_user"] > 0:
        
        # user who iniates this zero value transaction triggers a withdrawal to his address  
        ratio_initate_outcashing_and_all_zero_sendings = counts["count_zero_sending_paths"]["sc_sends_to_iniating_user"]/counts["count_zero_sending_paths"]["sends_zero_to_SC"]
        print("ratio_initate_outcashing_and_all_zero_sendings", ratio_initate_outcashing_and_all_zero_sendings)
        if ratio_initate_outcashing_and_all_zero_sendings > 0.2:
            scam_signal["zero_tx_used_to_pay_out"] = "Red"
        elif ratio_initate_outcashing_and_all_zero_sendings > 0.1 and ratio_initate_outcashing_and_all_zero_sendings <= 0.2:
            scam_signal["zero_tx_used_to_pay_out"] = "Orange"
        else:# <10%
            scam_signal["zero_tx_used_to_pay_out"] = "Green"

        # sc_sends_to_first_user
        ratio_sends_to_first_user_and_all_zero_sendings = counts["count_zero_sending_paths"]["sc_sends_to_first_user"]/counts["count_zero_sending_paths"]["sends_zero_to_SC"]
        print("ratio_sends_to_first_user_and_all_zero_sendings", ratio_sends_to_first_user_and_all_zero_sendings)
        if ratio_sends_to_first_user_and_all_zero_sendings > 0.2:
            scam_signal["zero_tx_used_to_payout_first_user"] = "Red"
        elif ratio_sends_to_first_user_and_all_zero_sendings > 0.1 and ratio_sends_to_first_user_and_all_zero_sendings <= 0.2:
            scam_signal["zero_tx_used_to_payout_first_user"] = "Orange"
        else:
            scam_signal["zero_tx_used_to_payout_first_user"] = "Green"
        

        # first_user_triggers_to_pay_out
        ratio_first_user_triggers_to_pay_out_and_all_zero_sendings = counts["count_zero_sending_paths"]["first_user_triggers_to_pay_out"]/counts["count_zero_sending_paths"]["sends_zero_to_SC"]
        print("ratio_first_user_triggers_to_pay_out_and_all_zero_sendings", ratio_first_user_triggers_to_pay_out_and_all_zero_sendings)
        if ratio_first_user_triggers_to_pay_out_and_all_zero_sendings > 0.2:
            print("More than 20% of all zero sending transactions are triggered by the first user")#withdrawals mainly from the first user
            scam_signal["P_most_of_zero_tx_are_from_first_user"] = "Red"
        elif ratio_first_user_triggers_to_pay_out_and_all_zero_sendings > 0.1 and ratio_first_user_triggers_to_pay_out_and_all_zero_sendings <= 0.2:
            scam_signal["P_most_of_zero_tx_are_from_first_user"] = "Orange"
        else:
            scam_signal["P_most_of_zero_tx_are_from_first_user"] = "Green"

        if ratio_first_user_triggers_to_pay_out_and_all_zero_sendings == ratio_sends_to_first_user_and_all_zero_sendings and ratio_sends_to_first_user_and_all_zero_sendings == ratio_initate_outcashing_and_all_zero_sendings and ratio_initate_outcashing_and_all_zero_sendings !=0:
            print("All triggered withdrawals are from the first user")
            scam_signal["P_withdrawal_function_just_from_first_user"] = "Red"
    else:
        print("No zero sending paths")





    #TODO here are all addresess before getting kicked because they have no value transactions
    howmany = 0
    for address in address_balance:
        howmany += 1
    print("nunber of all addresses before those without eth get kicked: ", howmany) # all addresses before getting kicked

    # kick out all addresses which have no value transactions ( interaction as sender or as receiver)
    address_balance = {address: values for address, values in address_balance.items() if values["interaction_as_sender"] > 0 or values["interaction_as_receiver"] > 0}
    #these addresses interacted with the SC but did not invest any ether or received any ether
    
    # Convert wei to ether
    def wei_to_ether(wei_value):
        return wei_value / 10**18
    
    # Save the results
    with open(f"output/address_balance_{filename_without_extension}.csv", "w") as f:
        f.write("address,received,invested,first_transaction,interactions_as_sender, interactions_as_receiver, first_interaction_as_sender\n")
        for address, values in address_balance.items():
            received_ether = wei_to_ether(values['received'])
            invested_ether = wei_to_ether(values['invested'])
            f.write(f"{address},{received_ether:.18f},{invested_ether:.18f},{values['first_transaction']},{values['interaction_as_sender']},{values['interaction_as_receiver']},{values['first_interaction_as_sender']}\n")
    
    ######### calculate
    print("Calculating the Ponzi criteria")
    # the SC has a special role in the Ponzi scheme, as it is the contract that receives the ether from the users and distributes it to the other users.
    # The SC is the address that receives the most ether from the users.
    sc_address = max(address_balance, key=lambda x: address_balance[x]["received"])
    print(f"The smart contract address with the most ether transfer is: {sc_address}")

    which_token = helper.get_kind_of_Sc(sc_input, node_url, likehood_threshold)
    if which_token == 2:
        print("The contract got doubled checked and is also no token contract")
    elif which_token == 1:
        print("token contract!\n In depth analysis for token contracts not implemented yet!\n It is recommended that the result be considered with a degree of caution, as it is based on the assumption that only native ether is involved.")

    # Addresses with no incoming transactions to the SC are considered to be the first users in the Ponzi scheme. They should have no first_transaction timestamp.
    users_with_no_input = [address for address in address_balance if address_balance[address]["invested"] == 0] # these are just the addresses which received but never sent
    #print(f"The first users in the Ponzi scheme are: {users_with_no_input}")



    ######### Requirements Bartoletti et al. (2019)
    print("Start with four requirements to check if the contract is a Ponzi scheme from Bartoletti et al. (2019)")

    #R1 logic
    # calculate how many users of all users have no incoming transactions to the SC
    number_of_users_with_no_input = len(users_with_no_input)
    total_number_of_users = len(address_balance)# only with value transaction. there more addresses with interactions but no value transactions
    percentage_of_users_with_no_input = number_of_users_with_no_input / total_number_of_users
    print(f"The percentage of users without input is : {percentage_of_users_with_no_input:.2f}")
    if percentage_of_users_with_no_input > likehood_threshold:
        # Rules out -> no ponzi
        print(f"The percentage of users without input is higher than the threshold of {likehood_threshold}. This means most of the users in this Contract are receiving ether from the SC. This is a strong indicator that this Contract is NOT a Ponzi scheme. And that the logic is external (R1)")
        # like a exchange with an address for inputs and an address for outputs. logic is not visible (R1)
        # so there logic that the addresess invested is likely on a centralized exchange
    else:
        # could be Ponzi if more requirements are met
        print("Most addresses are sending ether to the SC. This is a first indicator that this Contract COULD be Ponzi scheme.(R1)")
    # percentage_of_users_with_no_input < 10 % ROT; < 50%/or likehood ORANGE; < 90% GREEN
    #scam_signal
    if percentage_of_users_with_no_input < 0.1:
        scam_signal["R1"] = "Red"
    elif percentage_of_users_with_no_input >= 0.1 and percentage_of_users_with_no_input < likehood_threshold:
        scam_signal["R1"] = "Orange"
    else:
        scam_signal["R1"] = "Green"
    


    # calculate the profit of each user except the main SC
    # The profit of a user is the ether received minus the ether invested.
    user_profits = {address: address_balance[address]["received"] - address_balance[address]["invested"] for address in address_balance if address != sc_input}
    #TODO profit timestamp einbauen

    # median profit except the SC
    median_profit = sorted(user_profits.values())[len(user_profits) // 2]
    median_profit_in_eth = wei_to_ether(median_profit)
    print(f"The median profit of users is: {median_profit_in_eth} ETH")
    if median_profit > 0:
        print("The median profit of users is positive. This is a strong indicator that this Contract is NOT a Ponzi scheme.")
        scam_signal["A_median_profit"] = "Green"
    elif median_profit == 0:
        scam_signal["A_median_profit"] = "Orange"
    else:
        print("The median profit of users is negative. This is a strong indicator that this Contract is a Ponzi scheme.")
        scam_signal["A_median_profit"] = "Red"
    
    

    # Addition: Wie oft welche Summe vorkommt
    # check if users invest the same in most cases
    # check with which frequency the users invest the same amount of ether
   
    # Extract the "invested" amounts from the defaultdict, excluding zero values
    invested_amounts = [details["invested"] for details in address_balance.values() if details["invested"] != 0]

    # Count the frequency of each invested amount using Counter
    frequency = Counter(invested_amounts)

    # Identify the top 5 most frequent invested amounts
    top_5 = frequency.most_common(5)

    # Calculate the total occurrences of the top 5 amounts
    top_5_sum = sum(count for amount, count in top_5)

    # Calculate the total number of all non-zero invested occurrences
    total_sum = sum(frequency.values())

    # Calculate the percentage of the top 5 frequencies relative to the total
    top_5_percentage = (top_5_sum / total_sum)

    # Print the results
    print(f"Top 5 frequencies: {top_5}")
    print(f"Total occurrences of top 5: {top_5_sum}")
    print(f"Total non-zero invested occurrences: {total_sum}")
    print(f"Top 5 frequencies as a percentage of total: {top_5_percentage:.2f}")
    
    if top_5_percentage > likehood_threshold:
        print(f"The top 5 frequencies of invested amounts account for more than {likehood_threshold} of all non-zero invested occurrences. This is a strong indicator that this Contract is a Ponzi scheme because its a implemented logic.")
        # mostly the same amount invested, could be Ponzi if more requirements are met
        scam_signal["A_invested_amounts_frequency"] = "Red"
    elif top_5_percentage >= 0.5 and top_5_percentage <= likehood_threshold:
        scam_signal["A_invested_amounts_frequency"] = "Orange"
    else:
        print("sums are different")
        scam_signal["A_invested_amounts_frequency"] = "Green"



        #R2: only investors
    # check if the SC has an external investor (who has invested the most by far)
    # The user who has invested the most ether (and is not the SC) and did not make profit is considered to be the external investor. & did not joined as last.
    user_most_invested = max(
    (address for address in address_balance if address != sc_input),
    key=lambda x: address_balance[x]["invested"])
    print(f"The user who invested the most ether is: {user_most_invested}")
    # profit of the user who invested the most
    profit_of_user_most_invested = user_profits[user_most_invested]
    print(f"The profit (investment if negativ) of the user who invested the most is : {profit_of_user_most_invested}")
    timestamp_of_user_most_invested = address_balance[user_most_invested]["first_transaction"]
    print(f"The timestamp of the first transaction of the user who invested the most ether is: {timestamp_of_user_most_invested}")
    if last_timestamp == timestamp_of_user_most_invested and profit_of_user_most_invested < 0:
        # handover scheme -> Ponzi Red
        scam_signal["R2"] = "Red"
        print("The last timestamp is equal to the timestamp of the user who invested the most ether and this big investor loses money. This could be a strong indicator that this Contract is a Ponzi scheme.(R2)")#Red
    elif last_timestamp != timestamp_of_user_most_invested and profit_of_user_most_invested < 0:
        
        # external investor makes a loss
        print(" Could be an external source which pays off with own funds(R2)")
        # How big is the loss? Vergleich von von input zu output?
        if address_balance[user_most_invested]["received"] / address_balance[user_most_invested]["invested"] > 0.1:
            print("But this investor also gets a lot of ether back. perhaps not an external one after all  (R2)")#ORANGE
            scam_signal["R2"] = "Orange"
        else:
            # Rules out R2-> no ponzi
            print("Should be an external investor since he makes a loss and does not get much back (R2)")#Green
            scam_signal["R2"] = "Green"
    else: # big investor also makes profit
        # could also be Ponzi if more requirements are met
        print("Cant say anything about the contract(R2) since the biggest investor makes profit.")# Orange / neutral
        scam_signal["R2"] = "Orange"
    #TODO check whether this address is a sc?
    


    # addition?A_percentage_of_profitable_users
    # calculate how many users have a profit greater than 0
    profitable_users = [address for address in user_profits if user_profits[address] > 0]
    number_of_profitable_users = len(profitable_users) # this excludes all the profit/loss = 0 users
    percentage_of_profitable_users = number_of_profitable_users / total_number_of_users #TODO toal number of users are just the ones with value transactions
    print(f"The percentage of profitable users is: {percentage_of_profitable_users:.2f}")
    if percentage_of_profitable_users > likehood_threshold:
        print("The percentage of profitable users is higher than the threshold of 66.66%. This means most of the users in this Contract are making a profit. This is a strong indicator that this Contract is NOT a Ponzi scheme. ")
        # mostly profitable addresses/users
        # or in a early phase of Ponzi where almost all like in chain win?
        scam_signal["A_percentage_of_profitable_users"] = "Green"
    elif percentage_of_profitable_users >= 0.5 and percentage_of_profitable_users <= likehood_threshold:
        scam_signal["A_percentage_of_profitable_users"] = "Orange"
    else:
        print("Most users are not profitable. This is a first indicator that this Contract COULD be Ponzi scheme.")
        scam_signal["A_percentage_of_profitable_users"] = "Red"


    #R3
    # each investor makes profit if ENOUGH new investors send ENOUGH ether to the SC after his investment
    # unlucky gamers in casino should still lose money -> rules out R3
    #early einsteiger sollten also gewinn machen
    #user_profits[address] profits of a address
    # ratio of the sinking ratio of profit takers with the user growth
    anzahl_user_bis_jetzt = 0
    anzahl_profits_bis_jetzt = 0
    last_ratio = 0
    how_ofte_does_ratio_sink = 0
    for address in user_profits:
        anzahl_user_bis_jetzt += 1
        if user_profits[address] > 0: # if profit
            anzahl_profits_bis_jetzt += 1
        
        user_rataio = anzahl_profits_bis_jetzt/anzahl_user_bis_jetzt
        #print(user_rataio)
        if last_ratio > user_rataio:
            how_ofte_does_ratio_sink += 1

        last_ratio = user_rataio

    ratio_of_sinking_profit_takers_with_user_growth = how_ofte_does_ratio_sink/anzahl_user_bis_jetzt
    print("ratio_of_sinking_profit_takers_with_user_growth", ratio_of_sinking_profit_takers_with_user_growth)
    if ratio_of_sinking_profit_takers_with_user_growth > 0.5:
        print("When we check the profability of the users we see that the ratio of profitable users is sinking with reaching the end of the user growth (R3)")
        scam_signal["R3"] = "Red"
    elif ratio_of_sinking_profit_takers_with_user_growth == 0.5:
        print("The ratio of profitable users is constant with the user growth (R3)")
        scam_signal["R3"] = "Orange"
    else:
        print("The ratio of profitable users is increasing with the user growth (R3)")
        scam_signal["R3"] = "Green"



    #R4
    # Probability of losing money grows with the time of joining the scheme later
    # bubble chart? scatter plot?
    unprofitable_users = [address for address in user_profits if user_profits[address] < 0]
    even_profit_users = [address for address in user_profits if user_profits[address] == 0]
    
    # Extract all the timestamps of the first transaction for unprofitable users
    timestamps_unprofit = [address_balance[address]["first_transaction"] for address in unprofitable_users]
    
    # Convert each Timestamp to a Unix timestamp
    unix_timestamps_unprofit = [int(ts.timestamp()) for ts in timestamps_unprofit]

    # Calculate the average of the Unix timestamps
    average_unix_timestamp = sum(unix_timestamps_unprofit) / len(unix_timestamps_unprofit)
    # Convert the average Unix timestamp back to a Pandas Timestamp (humandreadable)
    average_timestamp = pd.to_datetime(average_unix_timestamp, unit='s')

    #print(f"The average Unix timestamp is: {average_unix_timestamp}")
    print(f"The average timestamp of unprofitable users is: {average_timestamp}")

    #average_timestamp_profitable_users müssen die None gefiltert werden. Sind profitbal ohne zu joinen?
    # users_with_no_input sind schon in R1 definiert die user ohne Input/timestamp


    # profit users which has timestamp. this means they invested once
    prof_user_with_timestamp = [address for address in user_profits if user_profits[address] > 0 and address_balance[address]["first_transaction"] is not None]
    if not prof_user_with_timestamp:
        print("There are no profitable users with investment-timestamps. (R4) ") # Orange
        scam_signal["R4"] = "Orange"
        # in scams should be at least one user who makes profit -> or its just the one without timestamp->hardcoded?
        timestamps_profit = None # just for plotting_tx
    else:
        ####Comparison of AVERAGE timestamps
        # Extract all the timestamps of the first transaction for profitable users with timestamp
        timestamps_profit = [address_balance[address]["first_transaction"] for address in prof_user_with_timestamp]
        # Convert each Timestamp to a Unix timestamp
        unix_timestamps_profit = [int(ts.timestamp()) for ts in timestamps_profit]
        # Calculate the average of the Unix timestamps
        average_unix_timestamp_profit = sum(unix_timestamps_profit) / len(unix_timestamps_profit)
        # Convert the average Unix timestamp back to a Pandas Timestamp (humandreadable)
        average_timestamp_profit = pd.to_datetime(average_unix_timestamp_profit, unit='s')
        # Print the average timestamp of profitable users
        print(f"The average timestamp of profitable users is: {average_timestamp_profit}")

        # check if the average timestamp of unprofitable users is greater than the average timestamp of profitable users
        if average_timestamp > average_timestamp_profit:
            print("The average entry timestamp of unprofitable users is greater than the average entry timestamp of profitable users. Likely Ponzi. (R4)")#Red
            scam_signal["R4"] = "Red"
        else:
            print("The average entry timestamp of unprofitable users is not greater than the average entry timestamp of profitable users. Likely not Ponzi. (R4)")#green
            scam_signal["R4"] = "Green"
    


    ##### Caclucate Data for Plotting_first_tx#####
    # Extract data for plotting_tx - Unprofitable users and profitable users with their invest/loss
    # their timestamps are already extracted in R4
    losses = [user_profits[address] for address in unprofitable_users]
    profits_profitable_with_timestamp = [user_profits[address] for address in prof_user_with_timestamp]

    # Extract data for plotting_tx - Even profit users
    timestamps_even_profit = [address_balance[address]["first_transaction"] for address in even_profit_users]
    profits_even_profit = [user_profits[address] for address in even_profit_users]

    # Extract data for plotting_tx - Profitable users with no original timestamp
    timestamps_profit_no_timestamp = [earliest_timestamp for address in users_with_no_input]# assign each user without timestamp with the earliest timestamp
    profits_profit_no_timestamp = [user_profits[address] for address in users_with_no_input]
    
    #Plotting_first_tx R4
    plotting_tx(timestamps_unprofit, losses, profits_profitable_with_timestamp, timestamps_profit, profits_even_profit, timestamps_even_profit, profits_profit_no_timestamp, timestamps_profit_no_timestamp, filename_without_extension, "Investment")
    

    
    ###Same with first_interaction_as_sender: same money but other timestamps
    timestamps_interaction_unprofit = [address_balance[address]["first_interaction_as_sender"] for address in unprofitable_users]
    timestamps_interaction_even = [address_balance[address]["first_interaction_as_sender"] for address in even_profit_users]

    prof_user_with_interaction = [address for address in user_profits if user_profits[address] > 0 and address_balance[address]["first_interaction_as_sender"] is not None]
    if not prof_user_with_interaction:
        print("There are no profitable users with interaction-timestamps. (R4) ")
        timestamps_interaction_profit = None # just for plotting_first_interaction
        profits_interaction = None
    else:
        timestamps_interaction_profit = [address_balance[address]["first_interaction_as_sender"] for address in prof_user_with_interaction]
        profits_interaction = [user_profits[address] for address in prof_user_with_interaction]
    
    #plotting_first_interaction()
    plotting_tx(timestamps_interaction_unprofit, losses, profits_interaction, timestamps_interaction_profit, profits_even_profit, timestamps_interaction_even, None, None, filename_without_extension, "Interaction")



    """
    # Example forsage:
    print(type(address_balance["0x4aaa7083535965d1cdd44d1407dcb11eec3f576d"]["first_transaction"]))
    # Extract all the timestamps
    timestamps = [value['first_transaction'] for value in address_balance.values()]
    print(address_balance["0x4aaa7083535965d1cdd44d1407dcb11eec3f576d"]["first_transaction"] > address_balance["0xee0e5160cc1d236ddd23c9340d1d687799100cb2"]["first_transaction"])
    print(address_balance["0x4aaa7083535965d1cdd44d1407dcb11eec3f576d"]["first_transaction"] - address_balance["0xee0e5160cc1d236ddd23c9340d1d687799100cb2"]["first_transaction"])
    print(address_balance["0x4aaa7083535965d1cdd44d1407dcb11eec3f576d"]["first_transaction"].isoformat())
    """


    print(scam_signal)
    # save the scam signal as txt file
    with open(f"output/scam_signal_{filename_without_extension}.txt", "w") as f:
        for key, value in scam_signal.items():
            f.write(f"{key}: {value}\n")
        
        #calculation of the scam signal here add the results
        #f.write("Potential scam :\n")
    
    # return output if scam as file?
    return address_balance


def check_ponzi_criteria(ocel, filename_without_extension, folder_path, node_url, likehood_threshold):
    print("Start checking Ponzi criteria:")
    # firstly check the ponzi if he is a contract or an EOA: extractor gives just trace tree output, when trying to extract a EOA address without creation

    """
    It's important to note that while events_df is a Pandas DataFrame, it's a view into the OCEL data structure. 
    If you modify this DataFrame, you may need to update the OCEL object to reflect these changes, depending on what operations you're performing
    events_df = ocel.events #ocel.events returns a Pandas DataFrame
    #print(ocel.objects)
    """

    input_output_flow(ocel, filename_without_extension, folder_path, node_url, likehood_threshold)
    #alignments_calculations(ocel)

  

    """
    Updating OCEL:
    After manipulating the DataFrame, how to update the OCEL object to reflect these changes?
    """
    return