from infrastructure import *
from config import *
import pandas as pd
import numpy as np
from pyclustering.cluster.kmeans import kmeans, kmeans_visualizer
from pyclustering.cluster.center_initializer import kmeans_plusplus_initializer
from pyclustering.utils.metric import type_metric, distance_metric
from pyclustering.samples.definitions import FCPS_SAMPLES
from pyclustering.utils import read_sample
from config import *
import osmnx as ox
import networkx as nx


df = query(qrestaurants)
              
#df['order_coordinates'] = list(zip(df.order_latitude, df.order_longitude))
#df['restaurant_coordinates'] = list(zip(df.rlat, df.rlon))


#X = df[['order_latitude', 'order_longitude']].to_numpy()
X = df[['address_latitude', 'address_longitude']].to_numpy()


'''
G = ox.graph_from_bbox(38.3764896, 38.2871322, -0.4099116, -0.5217002 )
graph_map = ox.plot_graph_folium(G, popup_attribute='name', edge_width=2)
'''

#ox.stats.basic_stats(G, area = 10000,  clean_intersects=True)
#ox.stats.extended_stats(G, connectivity=True, anc=True, ecc=True, bc=true, cc=True)

  

# plt.scatter(*zip(*X))
model = K_Means()
model.fit(X)

df['restaurant_coordinates'] = list(zip(df.address_latitude, df.address_longitude))              

lat_sample = np.arange(41.372371, 41.441524, 0.001).tolist()
lon_sample = np.arange(2.104855,2.231566, 0.001)
sampling_space = [[x,y] for x in lat_sample for y in lon_sample]
#sampling_space = np.asarray(sampling_space, dtype=np.float32)

'''
for i in range(len(sampling_space)): #Cambiar a nditer
    y = model.predict(sampling_space[i])
    print(y)
    if y == 0:
        plt.scatter(sampling_space[i][1], sampling_space[i][0], marker="x",color='b', s=15, linewidths=5)
      
plt.show()        
'''










class Soultion(self):
    pass



pol0 = []
pol1 = []
pol2 = []
pol3 = []
pol4 = []

for i in range(len(sampling_space)): #Cambiar a nditer
    y = model.predict(sampling_space[i])
    if y == 0:
        pol0.append(sampling_space[i])
    elif y == 1:
        pol1.append(sampling_space[i])
    elif y == 2:
        pol2.append(sampling_space[i])
    elif y == 3:
        pol3.append(sampling_space[i])
    elif y == 4:
        pol4.append(sampling_space[i])
    else:
        pass        


hull = shapely.geometry.MultiPoint(pol0).convex_hull.exterior._get_coords()

vertices = [list(v) for v in zip(hull.xy[0],hull.xy[1])]


plt.plot(hull.xy[1], hull.xy[0])





style.use('ggplot')
colors = ['blue', 'yellow','red']
for classification in model.classifications:
    color = colors[classification]
    for featureset in model.classifications[classification]:
        plt.scatter(featureset[1], featureset[0], marker="x",color=color, s=150, linewidths=5)
    

for centroid in model.centroids:
    plt.scatter(model.centroids[centroid][1], model.centroids[centroid][0], #imbecil
                marker="o", color="k", s=150, linewidths=5)
    
plt.show() 

     
mapBCN = folium.Map(location=[41.4469 ,2.2324 ],zoom_start = 10) 
colors = ['blue', 'yellow','red']
for classification in model.classifications:
    color = colors[classification]
    for featureset in model.classifications[classification]:
        folium.CircleMarker(location = [featureset[0], featureset[1]],radius=5,fill=True,
                            color = color).add_to(mapBCN) 


        
for centroid in model.centroids:
    lat = model.centroids[centroid][0]
    lon = model.centroids[centroid][1]
    coordenadas = str(lat) + ',' + str (lon)
    folium.Marker(location = [model.centroids[centroid][0], model.centroids[centroid][1]], popup = coordenadas, icon=folium.Icon(color='red', icon='info-sign')).add_to(mapBCN)      
        
mapBCN.save('mapa_rest.html')