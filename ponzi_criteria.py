import pm4py
import pandas as pd
import networkx as nx
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
"""
Auf forsage activites bezogen

# Load the OCEL file
def load_ocel(file_path):
    df = pd.read_csv(file_path, sep='\t')
    return df

# Create a transaction graph
def create_transaction_graph(df):
    G = nx.DiGraph()
    for _, row in df[df['ocel:activity'] == 'call and transfer ether'].iterrows():
        G.add_edge(row['from'], row['to'], value=float(row['callvalue']))
    return G

# Analyze payout structure
def analyze_payout_structure(df, G):
    payouts = {}
    for node in G.nodes():
        in_value = sum([G.edges[edge]['value'] for edge in G.in_edges(node)])
        out_value = sum([G.edges[edge]['value'] for edge in G.out_edges(node)])
        payouts[node] = {'in': in_value, 'out': out_value, 'net': in_value - out_value}
    return payouts

# Analyze user growth
def analyze_user_growth(df):
    registrations = df[df['ocel:activity'] == 'Registration'].sort_values('ocel:timestamp')
    registrations['cumulative_users'] = range(1, len(registrations) + 1)
    return registrations

# Analyze upgrade patterns
def analyze_upgrades(df):
    upgrades = df[df['ocel:activity'] == 'Upgrade'].sort_values('ocel:timestamp')
    return upgrades

# Main analysis function
def analyze_potential_ponzi(file_path):
    df = load_ocel(file_path)
    G = create_transaction_graph(df)
    
    payouts = analyze_payout_structure(df, G)
    user_growth = analyze_user_growth(df)
    upgrades = analyze_upgrades(df)
    
    # Calculate some metrics
    total_value = sum([payouts[node]['in'] for node in payouts])
    top_receivers = sorted(payouts.items(), key=lambda x: x[1]['net'], reverse=True)[:10]
    
    print(f"Total value in system: {total_value}")
    print("Top 10 net receivers:")
    for address, values in top_receivers:
        print(f"{address}: Net {values['net']}, In {values['in']}, Out {values['out']}")
    
    print(f"Total users: {len(user_growth)}")
    print(f"Total upgrades: {len(upgrades)}")
    
    # You could add more sophisticated analysis here, such as:
    # - Calculating the rate of user growth over time
    # - Analyzing the time between registration and first payout
    # - Checking for circular payment patterns
    # - Analyzing the referral structure

# Run the analysis
#analyze_potential_ponzi('path_to_your_ocel_file.csv')
"""

def load_bpmn_petri(filename_without_extension):
    #bpmn testen
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

def input_output_flow(ocel, filename_without_extension, folder_path, node_url, likehood_threshold):
    # Step 2: Extract relevant events and attributes
    events = ocel.events
    objects = ocel.objects
    
    # Step 3: Process the data
    address_balance = defaultdict(lambda: {"received": 0, "invested": 0, "first_transaction": None, "interaction_as_sender": 0, "interaction_as_receiver": 0})

    def update_balance(from_addr, to_addr, value):
        if from_addr:
            address_balance[from_addr]["invested"] += value
            address_balance[from_addr]["interaction_as_sender"] += 1
        if to_addr:
            address_balance[to_addr]["received"] += value
            address_balance[to_addr]["interaction_as_receiver"] += 1
    
    first_investment = {}
    for _, row in events.iterrows():
        if row["callvalue"] > 0:
            update_balance(row["from"], row["to"], row["callvalue"]) # Update the balance for the sender and receiver interacting with the contract

            # Check the timestamp of the first investment for each user = first transaction as sender (from)
            user = row["from"]
            timestamp = row["ocel:timestamp"]
            if user not in first_investment:
                first_investment[user] = timestamp
                address_balance[user]["first_transaction"] = timestamp
            else:
                first_investment[user] = min(first_investment[user], timestamp)
                address_balance[user]["first_transaction"] = timestamp
            

    
    # Convert wei to ether
    def wei_to_ether(wei_value):
        return wei_value / 10**18
    
    # Save the results
    with open(f"output/address_balance_{filename_without_extension}.csv", "w") as f:
        f.write("address,received,invested,first_transaction,interactions_as_sender, interactions_as_receiver\n")
        for address, values in address_balance.items():
            received_ether = wei_to_ether(values['received'])
            invested_ether = wei_to_ether(values['invested'])
            f.write(f"{address},{received_ether},{invested_ether},{values['first_transaction']},{values['interaction_as_sender']},{values['interaction_as_receiver']}\n")
    
    ######### calculate
    # the SC has a special role in the Ponzi scheme, as it is the contract that receives the ether from the users and distributes it to the other users.
    # The SC is the address that receives the most ether from the users.
    sc_address = max(address_balance, key=lambda x: address_balance[x]["received"])
    print(f"The smart contract address is: {sc_address}")
    #TODO double check by checking if its a EOA

    #which_token = ethereumnode.check_if_address_is_a_token(sc_address, node_url, likehood_threshold)
    #print("address is ",which_token)

    # Addresses with no incoming transactions to the SC are considered to be the first users in the Ponzi scheme. They should have no first_transaction timestamp.
    users_with_no_input = [address for address in address_balance if address_balance[address]["invested"] == 0]
    #print(f"The first users in the Ponzi scheme are: {users_with_no_input}")

    #R1
    # calculate how many users of all users have no incoming transactions to the SC
    number_of_users_with_no_input = len(users_with_no_input)
    total_number_of_users = len(address_balance)
    percentage_of_users_with_no_input = number_of_users_with_no_input / total_number_of_users
    print(f"The percentage of users without input is : {percentage_of_users_with_no_input:.2f}")
    if percentage_of_users_with_no_input > likehood_threshold:
        # Rules out -> no ponzi
        print("The percentage of users without input is higher than the threshold of 66.66%. This means most ofthe users in this Contract are receiving ether from the SC. This is a strong indicator that this Contract is NOT a Ponzi scheme. ")
        # like a exchange with an address for inputs and an address for outputs. logic is not visible (R1)
        # so there logic that the addresess invested is likely on a centralized exchange
    else:
        # could be Ponzi if more requirements are met
        print("Most addresses also sending ether to the SC. This is a first indicator that this Contract COULD be Ponzi scheme.")


    # calculate the profit of each user except the main SC
    # The profit of a user is the ether received minus the ether invested.
    user_profits = {address: address_balance[address]["received"] - address_balance[address]["invested"] for address in address_balance if address != sc_address}
    #TODO profit timestamp einbauen

    # median profit except the SC
    median_profit = sorted(user_profits.values())[len(user_profits) // 2]
    print(f"The median profit of users is: {median_profit:.2f}")
    
    

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
        print("The top 5 frequencies of invested amounts account for more than 66.66% of all non-zero invested occurrences. This is a strong indicator that this Contract is a Ponzi scheme because its a implemented logic.")
        # mostly the same amount invested, could be Ponzi if more requirements are met
    else:
        print("Frequency is different")
        # 



    #R2: only investors
    # check if the SC has an external investor (who has invested the most by far)
    # The user who has invested the most ether (and is not the SC) and did not make profit is considered to be the external investor. & did not joined as last.
    user_most_invested = max(
    (address for address in address_balance if address != sc_address),
    key=lambda x: address_balance[x]["invested"])
    print(f"The user who invested the most ether is: {user_most_invested}")
    # profit of the user who invested the most
    profit_of_user_most_invested = user_profits[user_most_invested]
    print(f"The profit (investment) is : {profit_of_user_most_invested}")
    


    #R1+R2
    # calculate how many users have a profit greater than 0
    profitable_users = [address for address in user_profits if user_profits[address] > 0]
    number_of_profitable_users = len(profitable_users)
    percentage_of_profitable_users = number_of_profitable_users / total_number_of_users
    print(f"The percentage of profitable users is: {percentage_of_profitable_users:.2f}")
    if percentage_of_profitable_users > likehood_threshold:
        print("The percentage of profitable users is higher than the threshold of 66.66%. This means most of the users in this Contract are making a profit. This is a strong indicator that this Contract is NOT a Ponzi scheme. ")
        # mostly profitable addresses/users which kicks SEC (R1+R2)
        # or in a early phase of Ponzi where almost all like in chain win?
    else:
        print("Most users are not profitable. This is a first indicator that this Contract COULD be Ponzi scheme.")


    #TODO check mittels helper datei ob addresse eoa oder sc ist
    #address_dict = helper.open_address_file(folder_path, filename_without_extension)
    #print(address_dict["0xfffc07f1b5f1d6bd365aa1dbc9d16b1777f406a2"])

    return address_balance


def check_ponzi_criteria(ocel, filename_without_extension, folder_path, node_url, likehood_threshold):
    print("Start checking Ponzi criteria:")
    # firstly check the ponzi if he is a contract or an EOA: extractor gives just trace tree output, when trying to extract a EOA address without creation

    """
    # netwrokx testen:
    G = pm4py.convert.convert_ocel_to_networkx(ocel)
    #print(G)
    edge_types = set(nx.get_edge_attributes(G, 'type').values())
    #print("Edge types:", edge_types)
    """

    """
    It's important to note that while events_df is a Pandas DataFrame, it's a view into the OCEL data structure. 
    If you modify this DataFrame, you may need to update the OCEL object to reflect these changes, depending on what operations you're performing
    """
    events_df = ocel.events #ocel.events returns a Pandas DataFrame
    #print(ocel.objects)

    input_output_flow(ocel, filename_without_extension, folder_path, node_url, likehood_threshold)
    

    """
    #check if token functions implemented 
    main_smart_contract = filename_without_extension.split('_')[0]
    print("Main smart contract:", main_smart_contract)
    #TODO als main address eher sc_address aus input_output_flow nehmen, welche die meisten ether erhalten hat
    which_token = ethereumnode.check_if_address_is_a_token(main_smart_contract, node_url, likehood_threshold)
    print("address is ",which_token)
    """


    """
    my own BPMN
    
    net, initial_marking, final_marking = load_bpmn_petri(filename_without_extension)

    traditional_log = ocel_flattening.flatten(ocel, "ocel:type:Address_o") # gegebenenfalls noch from_o addresse als objekt
    replayed_traces = pm4py.conformance_diagnostics_token_based_replay(traditional_log, net, initial_marking, final_marking)
    print(replayed_traces)
    """

    """
    Updating OCEL:
    After manipulating the DataFrame, you can update the OCEL object:
    pythonCopyocel.events = modified_events_df
    ocel.objects = modified_objects_df
    """
    return