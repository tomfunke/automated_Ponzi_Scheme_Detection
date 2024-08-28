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
import pm_discovery


def load_bpmn_petri(filename_without_extension):
    """
    bpmn to petri net
    returns the petri net
    """

    # Load the BPMN file
    bpmn_graph = bpmn_importer.apply("input/ponzi.bpmn")
    
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
        plt.scatter(timestamps_even_profit, profits_even_profit, color='orange', label='Even Profit Users')

    # Plot profitable users with no original timestamp in orange
    if timestamps_profit_no_timestamp and profits_profit_no_timestamp:
        plt.scatter(timestamps_profit_no_timestamp, profits_profit_no_timestamp, color='blue', label='Profit - No Original Timestamp')


    # Add labels and title
    plt.xlabel(f"Timestamp of First {which_timestamp}")
    plt.ylabel('Profit in Wei')
    plt.title(f"Profit distribution of the smart contract \n {filename_without_extension}")

    #Automatically Adjusting the X-Axis Limits
    #plt.xlim([min(timestamps_unprofit + timestamps_profit), max(timestamps_unprofit + timestamps_profit)])

    # Set the x-axis limits manually
    #plt.xlim(pd.Timestamp('2016-02-16'), pd.Timestamp('2016-08-16')) # ether_doubler_without_deployer has outlier in 2018

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

def input_output_flow(ocel, filename_without_extension, folder_path, node_url, likehood_threshold, combined_df):
    # Step 1: Extract relevant events and attributes
    events = ocel.events
    objects = ocel.objects
    
    # Step 2: 

    # first row
    first_row = events.iloc[0]
    deployment_address = first_row["from"]
    first_input = first_row["input"]
    first_user = []
    address_dict = helper.open_address_file(folder_path, filename_without_extension)
    
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
    first_user.append(deployment_address)

    print(first_user)
    #print(address_dict["0xfffc07f1b5f1d6bd365aa1dbc9d16b1777f406a2"])# if eoa or sc

    # get important timestamps of the events
    last_timestamp = events["ocel:timestamp"].max()
    print("Last timestamp:", last_timestamp)
    earliest_timestamp = events["ocel:timestamp"].min()

    # get the SC address
    sc_input = helper.get_contract_address_from_blockrange_name(filename_without_extension)

    # Step 3: Process the data
    address_balance = defaultdict(lambda: {"received": 0, "invested": 0, "first_transaction": None, "interaction_as_sender": 0, "interaction_as_receiver": 0, "first_interaction_as_sender": None})

    def update_balance(from_addr, to_addr, value):
        if from_addr:
            address_balance[from_addr]["invested"] += value
            address_balance[from_addr]["interaction_as_sender"] += 1
        if to_addr:
            address_balance[to_addr]["received"] += value
            address_balance[to_addr]["interaction_as_receiver"] += 1
    
    # count the different paths of the transactions
    counts = {"count_initial_paths": None, "count_other_paths": None}
    counts["count_initial_paths"] = {"initial_investment_to_Sc_by_EOA": 0,
                    "Sc_sends_to_another_user_in_same_transaction": 0,
                    "Sc_sends_to_multiple_users_in_same_transaction": 0,
                    "SC_does_not_send_to_others_in_same_transaction": 0,
                    "Internal_Upgrade_Event": 0,
                    "sc_sends_to_iniating_user" : 0,
                    "sc_sends_to_first_user" : 0,
                    "first_user_triggers_to_pay_out" : 0
                   }
    counts["count_other_paths"] = {"sends_zero_to_SC": 0,  "joins_without_investing": 0,
                    "Sc_sends_to_another_user_in_same_transaction": 0,
                    "Sc_sends_to_multiple_users_in_same_transaction": 0,
                    "SC_does_not_send_to_others_in_same_transaction": 0,
                    "Internal_Upgrade_Event": 0,
                    "sc_sends_to_iniating_user" : 0,
                    "sc_sends_to_first_user" : 0,
                    "first_user_triggers_to_pay_out" : 0
                    }
    counts["counter_user_sends_again_paths"] = {"invests_again": 0,
                    "Sc_sends_to_another_user_in_same_transaction": 0,
                    "Sc_sends_to_multiple_users_in_same_transaction": 0,
                    "SC_does_not_send_to_others_in_same_transaction": 0,
                    "Internal_Upgrade_Event": 0,
                    "sc_sends_to_iniating_user" : 0,
                    "sc_sends_to_first_user" : 0,
                    "first_user_triggers_to_pay_out" : 0
                    }
    
    def innerloop_for_same_tx_hash(i, events, hash_of_this_tx, pathing_type):
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
                    
            
            # check if events
            if "address" in inner_row:
                if inner_row["address"] == sc_input:
                    ####print("Internal Upgrade Event")
                    memory_of_this_hash["counter_how_often_internal_upgrade_event"] += 1
        
        return
    
    print(combined_df["concept:name"][0])
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
                    #combined_df["concept:name"][i+1] = "Initial Investment of User" # does not work-> idea to manipulate the events
                    combined_df.loc[i+1, "concept:name"] = "user A initiates Transaction"
                    counts["count_initial_paths"]["initial_investment_to_Sc_by_EOA"] += 1

                    innerloop_for_same_tx_hash(i, events, row["hash"], "count_initial_paths")
            
            
            # Not first transaction of the user
            elif address_balance[user]["first_transaction"] != None:
                if (row["from_Type"] == "EOA"):
                    # its an EOA
                    ###print("investor is multiple times investing: ", user)
                    counts["counter_user_sends_again_paths"]["invests_again"] += 1
                    # TODO was passiert wenn ein user mehrmals investiert? -> wie wird das in der Abfgole berücksichtigt?
                    innerloop_for_same_tx_hash(i, events, row["hash"], "counter_user_sends_again_paths")
                    
        
        else: # no value in this transaction
            # Also events will be counted here AGAIN->wrongly
            # TODO calltype empty -> events
            #if row["address"] == sc_input:
            #    print("nochamal gezählt?")

            # if callvalue is 0 and someone is sending to the SC means its a trigger from outside the SC
            if(row["to"] == sc_input):
                ##print(user, " triggers from outside the SC")

                # TODO joining without investing
                # first interaction and event happens but not value is sent
                if address_balance[user]["first_interaction_as_sender"] == None:
                    counts["count_other_paths"]["joins_without_investing"] += 1
                
                # add timestamp for first interaction as sender
                if address_balance[user]["first_interaction_as_sender"] == None:
                    address_balance[user]["first_interaction_as_sender"] = timestamp
                    ##print("First interaction of user: ", user)
                
                counts["count_other_paths"]["sends_zero_to_SC"] += 1
                #TODO test if the SC sends to another user like in 0xa068bdda7b9f597e8a2eb874285ab6b864836cb8e48a1b6fccb0150bf44f5592 #coinbase ODER 0xa068bdda7b9f597e8a2eb874285ab6b864836cb8e48a1b6fccb0150bf44f5592 chicken
                # same hash should have callvalue > 0 and from = SC and to = user
                innerloop_for_same_tx_hash(i, events, row["hash"], "count_other_paths")
                #otherwise event triggering without funds moving?
                #like gaming /attacking 
                
    
    # print initial_investment_to_Sc_by_EOA
    print(counts["count_initial_paths"])
    # bedeuted es jetzt bei coinbase {'initial_investment_to_Sc_by_EOA': 156, 'Sc_sends_to_another_user_in_same_transaction': 0, 'Sc_sends_to_multiple_users_in_same_transaction': 0, 'SC_does_not_send_to_others_in_same_transaction': 156, 'Internal_Upgrade_Event': 0}
    # wenn alles 0 ist, dass es kein Ponzi ist? die Überweisung endet halt nur vor erst hier. Kann ja durch 0 callvalue noch getriggert werden
    
    print(counts["count_other_paths"])

    print(counts["counter_user_sends_again_paths"])
                        
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
            f.write(f"{address},{received_ether},{invested_ether},{values['first_transaction']},{values['interaction_as_sender']},{values['interaction_as_receiver']},{values['first_interaction_as_sender']}\n")
    
    ######### calculate
    print("Calculating the Ponzi criteria")
    # the SC has a special role in the Ponzi scheme, as it is the contract that receives the ether from the users and distributes it to the other users.
    # The SC is the address that receives the most ether from the users.
    sc_address = max(address_balance, key=lambda x: address_balance[x]["received"])
    print(f"The smart contract address with the most ether transfer is: {sc_address}")
    #TODO double check by checking if its a SC

    which_token = helper.get_kind_of_Sc(sc_input, node_url, likehood_threshold)
    if which_token == 2:
        print("The contract got doubled checked and is also no token contract")
    elif which_token == 1:
        print("token contract")

    # Addresses with no incoming transactions to the SC are considered to be the first users in the Ponzi scheme. They should have no first_transaction timestamp.
    users_with_no_input = [address for address in address_balance if address_balance[address]["invested"] == 0]
    #print(f"The first users in the Ponzi scheme are: {users_with_no_input}")

    #R1 logic
    # calculate how many users of all users have no incoming transactions to the SC
    number_of_users_with_no_input = len(users_with_no_input)
    total_number_of_users = len(address_balance)
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


    # calculate the profit of each user except the main SC
    # The profit of a user is the ether received minus the ether invested.
    user_profits = {address: address_balance[address]["received"] - address_balance[address]["invested"] for address in address_balance if address != sc_input}
    #TODO profit timestamp einbauen

    # median profit except the SC
    median_profit = sorted(user_profits.values())[len(user_profits) // 2]
    median_profit_in_eth = wei_to_ether(median_profit)
    print(f"The median profit of users is: {median_profit_in_eth} ETH")
    
    

    # Zusatz Wie oft welche Summe vorkommt
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
    else:
        print("sums are different")
        # 



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
        # handover scheme -> Ponzi
        print("The last timestamp is equal to the timestamp of the user who invested the most ether and this big investor loses money. This could be a strong indicator that this Contract is a Ponzi scheme.(R2)")#Red
    elif last_timestamp != timestamp_of_user_most_invested and profit_of_user_most_invested < 0:
        # Rules out R2-> no ponzi
        # external investor makes a loss
        print(" Could be an external source which pays off with own funds(R2)")
        # How big is the loss? Vergleich von von input zu output?
        if address_balance[user_most_invested]["received"] / address_balance[user_most_invested]["invested"] > likehood_threshold:
            print("But this investor also gets a lot of ether back. perhaps not an external one after all  (R2)")#ORANGE
        else:
            print("Should be an external investor since he makes a loss and does not get much back (R2)")#Green
    else: # big investor also makes profit
        # could also be Ponzi if more requirements are met
        print("Cant say anything about the contract(R2) since the biggest investor makes profit.")# Orange / neutral
    #TODO check whether this address is a sc?
    


    # zusatz?
    # calculate how many users have a profit greater than 0
    profitable_users = [address for address in user_profits if user_profits[address] > 0]
    number_of_profitable_users = len(profitable_users)
    percentage_of_profitable_users = number_of_profitable_users / total_number_of_users
    print(f"The percentage of profitable users is: {percentage_of_profitable_users:.2f}")
    if percentage_of_profitable_users > likehood_threshold:
        print("The percentage of profitable users is higher than the threshold of 66.66%. This means most of the users in this Contract are making a profit. This is a strong indicator that this Contract is NOT a Ponzi scheme. ")
        # mostly profitable addresses/users
        # or in a early phase of Ponzi where almost all like in chain win?
    else:
        print("Most users are not profitable. This is a first indicator that this Contract COULD be Ponzi scheme.")


    #R3
    # each investor makes profit if he is not the last investor/ new investors send ether to the SC after his investment
    # unlucky gamers in casino should still lose money -> rules out R3


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
        else:
            print("The average entry timestamp of unprofitable users is not greater than the average entry timestamp of profitable users. Likely not Ponzi. (R4)")#green
    


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




    # return output if scam as file?
    return events


def check_ponzi_criteria(ocel, filename_without_extension, folder_path, node_url, likehood_threshold, combined_df):
    print("Start checking Ponzi criteria:")
    # firstly check the ponzi if he is a contract or an EOA: extractor gives just trace tree output, when trying to extract a EOA address without creation

    """
    It's important to note that while events_df is a Pandas DataFrame, it's a view into the OCEL data structure. 
    If you modify this DataFrame, you may need to update the OCEL object to reflect these changes, depending on what operations you're performing
    events_df = ocel.events #ocel.events returns a Pandas DataFrame
    #print(ocel.objects)
    """

    man_combined_df = input_output_flow(ocel, filename_without_extension, folder_path, node_url, likehood_threshold, combined_df)
    #alignments_calculations(ocel)

    print("ocel converting...")

    print(combined_df.columns)

    
    
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
    #pm4py.write_ocel_csv(ocel, os.path.join(folder_path,'df_ocel_events_' + contract_file_name + ".csv"),os.path.join(folder_path,'df_ocel_objects_' + contract_file_name + ".csv"))

    #pm_discovery.pn_and_dfg_discovery(ocel, filename_without_extension)
    alignments_calculations(ocel)
    """
    Updating OCEL:
    After manipulating the DataFrame, how to update the OCEL object to reflect these changes?
    """
    return