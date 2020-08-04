from infrastructure import query
from MyKMeans import K_Means
import Clustered
import numpy as np
import shapely
import matplotlib.pyplot as plt
from matplotlib import style
import folium
from config import *
#import osmnx as ox


location = clusterer(60,80)
location.kmeans()

for location in locations:
    
    if hull(location).contains(points):
        
        location.append(points)
    
    hubs = location.Xmeans()   
    hubs.teselado()
    
        for hub in hubs:
            pools = hub.Xmeans()
            pools.teselado()
            simulate.run()

