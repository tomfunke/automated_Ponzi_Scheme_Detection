import pm4py
import pandas as pd

#Reference paper: van der Aalst, Wil MP, and Alessandro Berti. “Discovering object-centric Petri nets.” Fundamenta informaticae 175.1-4 (2020): 1-40

def pn_and_dfg_discovery(ocel):
    #print(ocel.get_extended_table())
    
    #Print some basic statisctics on ocels
    #print(ocel)
    #print(pm4py.ocel_get_object_types(ocel))
    #print(pm4py.ocel_object_type_activities(ocel))
    #print(pm4py.ocel_temporal_summary(ocel))
    #print(pm4py.ocel_objects_summary(ocel))
    
    
    # Discover an Object-Centric Petri Net (OC-PN) from the sampled OCEL
    ocpn = pm4py.discover_oc_petri_net(ocel) # Inductive Miner?
    # views the model
    pm4py.view_ocpn(ocpn, format="svg")

    # Discover an Object-Centric directly-follows multigraphs (OC-DFG) from the sampled OCEL
    ocdfg = pm4py.discover_ocdfg(ocel)
    # views the model with the frequency annotation
    pm4py.view_ocdfg(ocdfg, format="svg")
    # views the model with the performance annotation
    #pm4py.view_ocdfg(ocdfg, format="svg", annotation="performance", performance_aggregation="median")
    