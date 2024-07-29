import pm4py
import pandas as pd
from pm4py.objects.ocel.util import flattening as ocel_flattening


#Reference paper: van der Aalst, Wil MP, and Alessandro Berti. “Discovering object-centric Petri nets.” Fundamenta informaticae 175.1-4 (2020): 1-40

def pn_and_dfg_discovery(ocel, filename_without_extension):
    # filename_without_extension is for saving the output with the same name as input file
    print("Begin discovery:")

    """
    Transforms the current OCEL data structure into a Pandas dataframe containing the events with their attributes and the related objects per object type."
     https://pm4py.fit.fraunhofer.de/static/assets/api/2.7.11/pm4py.objects.ocel.html#pm4py.objects.ocel.obj.OCEL.get_extended_table
    """
    #df_ocel = ocel.get_extended_table()
    #print(df_ocel)
    
    #Print some basic statisctics on ocels
    print(ocel)
    #print(pm4py.ocel_get_object_types(ocel))
    #print(pm4py.ocel_object_type_activities(ocel))
    #print(pm4py.ocel_temporal_summary(ocel))
    #print(pm4py.ocel_objects_summary(ocel)) # life cycle of the objects
    print(pm4py.ocel_objects_summary(ocel))
    
    
    # Discover an Object-Centric Petri Net (OC-PN) from the sampled OCEL
    ocpn = pm4py.discover_oc_petri_net(ocel) # Inductive Miner?
    # views the model
    pm4py.view_ocpn(ocpn, format="svg")
    #Saves the visualization of the object-centric Petri net into a file
    pm4py.save_vis_ocpn(ocpn, f'output/ocPN_{filename_without_extension}.png', annotation='frequency')

    # Discover an Object-Centric directly-follows multigraphs (OC-DFG) from the sampled OCEL
    ocdfg = pm4py.discover_ocdfg(ocel)
    # views the model with the frequency annotation
    pm4py.view_ocdfg(ocdfg, format="svg")
    #save the model as png
    pm4py.save_vis_ocdfg(ocdfg, f'output/ocDFG_{filename_without_extension}.png', annotation='frequency')

    # views the model with the performance annotation
    ##pm4py.view_ocdfg(ocdfg, format="svg", annotation="performance", performance_aggregation="median")

    """
    # for bpmn you need to convert the ocel into xes by flattening
    # Assuming 'ocel' is your Object-Centric Event Log
    # Also need a ocel type to flatten
    traditional_log = ocel_flattening.flatten(ocel, "ocel:type:Address_o") # gegebenenfalls noch from_o addresse als objekt

    bpmn_model = pm4py.discover_bpmn_inductive(traditional_log)
    pm4py.view_bpmn(bpmn_model)
    pm4py.save_vis_bpmn(bpmn_model, f'output/BPMN_{filename_without_extension}.png')
    """