import pm4py
import pandas as pd
import networkx as nx
from datetime import datetime
from pm4py.objects.bpmn.importer import importer as bpmn_importer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.objects.conversion.bpmn import converter as bpmn_converter
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter

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

def check_ponzi_criteria(ocel, filename_without_extension):
    print("Start checking Ponzi criteria:")
    print(pm4py.ocel_objects_summary(ocel)) # life cycle of the objects


    df_ocel = ocel.get_extended_table() # The extended table "flattens" the structure, making it easier to analyze with traditional process mining techniques.
    print(df_ocel)
    # try pandas an ocel
    df = pd.DataFrame(df_ocel)
    print(df.head())

    # funktionen testen:
    G = pm4py.convert.convert_ocel_to_networkx(ocel)
    print(G)
    edge_types = set(nx.get_edge_attributes(G, 'type').values())
    print("Edge types:", edge_types)

    #bpmn testen
    # Load the BPMN file
    #bpmn_graph = bpmn_importer.apply('/Users/tomfunke/Desktop/diagram_1.bpmn')
    #bpmn_graph = bpmn_importer.apply("/Users/tomfunke/Downloads/diagram.bpmn")
    bpmn_graph = bpmn_importer.apply("input/ponzi.bpmn")
    

    # Visualize the BPMN
    ##gviz = bpmn_visualizer.apply(bpmn_graph)
    ##bpmn_visualizer.view(gviz)

    # Convert BPMN to Petri net 
    net, initial_marking, final_marking = bpmn_converter.apply(bpmn_graph)
    print(net)
    print(initial_marking)
    print(final_marking)
    print("Places in the net:", net.places)
    print("Transitions in the net:", net.transitions)

    # Generate the visualization of the Petri net
    gviz = pn_visualizer.apply(net, initial_marking, final_marking)

    # Display the visualization (this will open in a new window)
    pn_visualizer.view(gviz)

    # Save as PNG
    pn_visualizer.save(gviz, f'output/petri_net_visualization_{filename_without_extension}.png')
    
    # Save the Petri net in PNML format
    pnml_exporter.apply(net, initial_marking, f'output/saved_petri_net_{filename_without_extension}.pnml')
    

    """
    It's important to note that while events_df is a Pandas DataFrame, it's a view into the OCEL data structure. 
    If you modify this DataFrame, you may need to update the OCEL object to reflect these changes, depending on what operations you're performing
    """
    events_df = ocel.events #ocel.events returns a Pandas DataFrame
    """
    Updating OCEL:
    After manipulating the DataFrame, you can update the OCEL object:
    pythonCopyocel.events = modified_events_df
    ocel.objects = modified_objects_df
    """
    return