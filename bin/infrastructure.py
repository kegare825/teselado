'''
Introduce aqui las funciones principales que use main
'''

import pandas as pd
import networkx as nx
import osmnx as ox
import scipy.stats as st
from google.cloud import bigquery




#TODO Mirar como introducir metricas personalizadas en la libreria
def metrica(centroide, punto):
    nodo_centroide = ox.get_nearest_node(G, (centroide))
    nodo_punto =  ox.get_nearest_node(G, (punto))
    return nx.shortest_path_length(G, nodo_centroide, nodo_punto) 

def bounding_box(coords):
    #TODO mejorar el return para que lo acepte directamente ox.graph
    min_x = max_x = coords[0][0]
    min_y = max_y = coords[0][1]
    
    for item in coords:
      if item[0] < min_x:
        min_x = item[0]
    
      if item[0] > max_x:
        max_x = item[0]
    
      if item[1] < min_y:
        min_y = item[1]
    
      if item[1] > max_y:
        max_y = item[1]
    
    return [(min_x,min_y),(max_x,min_y),(max_x,max_y),(min_x,max_y)]              

def metrica(centroide, G):
    nodo_centroide = ox.get_nearest_node(G, (centroide))
    nodo_punto =  ox.get_nearest_node(G, (punto))
    return nx.shortest_path_length(G, nodo_centroide, nodo_punto) 

import scipy.stats as st

def get_best_distribution(data):
    dist_names = ["norm", "exponweib", "weibull_max", "weibull_min", "pareto", "genextreme"]
    dist_results = []
    params = {}
    for dist_name in dist_names:
        dist = getattr(st, dist_name)
        param = dist.fit(data)
    
        params[dist_name] = param
        # Applying the Kolmogorov-Smirnov test
        D, p = st.kstest(data, dist_name, args=param)
        print("p value for "+dist_name+" = "+str(p))
        dist_results.append((dist_name, p))
    
    # select the best fitted distribution
    best_dist, best_p = (max(dist_results, key=lambda item: item[1]))
    # store the name of the best fit and its p value
    
    print("Best fitting distribution: "+str(best_dist))
    print("Best p value: "+ str(best_p))
    print("Parameters for the best fit: "+ str(params[best_dist]))
    
    return best_dist, best_p, params[best_dist]

class Soultion:
    pass

