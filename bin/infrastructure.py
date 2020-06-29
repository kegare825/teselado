'''
Introduce aqui las funciones principales que use main
'''



import pandas as pd
import shapely
import networkx as nx
import osmnx as ox
import random
import math
import osmnx as ox
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
import folium
from config import *
import scipy.stats as st


def query(query_string: str) -> pd.DataFrame:
    """Query."""
    from google.cloud import bigquery
    default_project_id = 'REDACTED_GCP_PROJECT'
    client = bigquery.Client(project=default_project_id)
    job_config = bigquery.QueryJobConfig()
    query_job = client.query(query_string, job_config=job_config)
    return query_job.result().to_dataframe()


def bounding_box(coords):
#TODO mejorar el return para que lo acepte directamente ox.graph
  min_x = 100000 # start with something much higher than expected min
  min_y = 100000
  max_x = -100000 # start with something much lower than expected max
  max_y = -100000

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


def metrica(centroide, punto):
    nodo_centroide = ox.get_nearest_node(G, (centroide))
    nodo_punto =  ox.get_nearest_node(G, (punto))
    return nx.shortest_path_length(G, nodo_centroide, nodo_punto) 


class K_Means:
  def __init__(self, k=3, tol=0.001, max_iter=3000):
      self.k = k
      self.tol = tol
      self.max_iter = max_iter

  def fit(self,data):

      self.centroids = {}

      for i in range(self.k):
          self.centroids[i] = data[i]

      for i in range(self.max_iter):
          self.classifications = {}

          for i in range(self.k):
              self.classifications[i] = []

          for featureset in data:
              #distances = [metrica(centroid, featureset) for centroid in self.centroids]
              distances = [1.3*np.linalg.norm(featureset-self.centroids[centroid]) for centroid in self.centroids]

              classification = distances.index(min(distances))
              self.classifications[classification].append(featureset)

          prev_centroids = dict(self.centroids)

          for classification in self.classifications:
              self.centroids[classification] = np.average(self.classifications[classification],axis=0)

          optimized = True

          for c in self.centroids:
              original_centroid = prev_centroids[c]
              current_centroid = self.centroids[c]
              if np.sum((current_centroid-original_centroid)/original_centroid*100.0) > self.tol:
                  optimized = False

          if optimized:
              break

  def predict(self,data):
      distances = [np.linalg.norm(data-self.centroids[centroid]) for centroid in self.centroids]
      classification = distances.index(min(distances))
      return classification
  


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

class Soultion(self):
    pass

