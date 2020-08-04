# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 19:07:16 2020

@author: Carlos Morera & Aaron
"""
from pyclustering.cluster.kmeans import kmeans, kmeans_visualizer
from pyclustering.cluster.center_initializer import kmeans_plusplus_initializer
from pyclustering.cluster import cluster_visualizer
from pyclustering.cluster.fcm import fcm
from infrastructure import boundingbox
import numpy as np


class Clustered:
    
    
    def __init__(self, start=60, end=80): # metric=metrica#):
        """
        Class constructor
        
        Parameters
        ----------
        start : int 
            starting number of clusters
        end : int (optional)
            Ending number of clusters
        metric : function (optional)
            Metric used in the algorithm. The default value is the lambda
            function lambda c, e : 1.3*np.linalg.norm(e - c).
            
        Returns
        -------
        Constructed K_Means class.
        """
        self.__start = start
        self.__end = end
        self.__dabest = []
        
    
    def __kmeans(self, points):
        """
        Returns clusterization of dataset
        
        Parameters
        ----------
        points: list 
                        
        Returns
        -------
        Labeled class and center location
        """
        # Prepare initial centers using K-Means++ method.
        initial_centers = kmeans_plusplus_initializer(points, 10).initialize()
        # Create instance of K-Means algorithm with prepared centers.
        self.__kmeans_instance = kmeans(sample, initial_centers)
        # Run cluster analysis and obtain results.
        kmeans_instance.process()
        kclusters = kmeans_instance.get_clusters()
        kcenters = kmeans_instance.get_centers()
        return kclusters, kcenters

    def __cmeans(self, points, nclusters):
        """
        Returns fuzzy clusterization of dataset
        
        Parameters
        ----------
        points: list 
                        
        Returns
        -------
        Labeled class, membership,  and center location
        """
        # load list of points for cluster analysis
        # initialize
        initial_centers = kmeans_plusplus_initializer(points, nclusters, kmeans_plusplus_initializer.FARTHEST_CENTER_CANDIDATE).initialize()
        # create instance of Fuzzy C-Means algorithm
        fcm_instance = fcm(points, initial_centers)
        # run cluster analysis and obtain results
        fcm_instance.process()
        clusters = fcm_instance.get_clusters()
        centers = fcm_instance.get_centers()
        membership = fcm_instance.get_membership()
        return cclusters, ccenters, membership
    
    def get_clusters(self,points):
        """
        Returns clusterization of dataset
        
        Parameters
        ----------
        points: list 
                        
        Returns
        -------
        Returns best clusters candidates
        """
        self.points = points
        self.__dabest = [self.__cmeans(points,i) for i in range(self.__start,self.__end)]
        ##self.hull = 
        return self.__dabest


    def teselado(self,points):
        """
        Uses former clusteriation results to return an aproximate Voronoi
        tesselation of the city.
        
        Parameters
        ----------
        points: list
            
        Returns
        -------
        hull: list of the convex hull for each sample
        
        """
        #muestrea todo el espacio de la envolvente para conseguir las fronteras de decision a intervalos regulares 
        #get_hull
        area = boundingbox(points)
        #(min_x,min_y),(max_x,min_y),(max_x,max_y),(min_x,max_y)
        #sample inside hull
        lat_sample = np.arange(min_y, max_y, 0.001).tolist()
        lon_sample = np.arange(min_x,max_x, 0.001)
        sampling_space = [[x,y] for x in lat_sample for y in lon_sample]
        sampling_space = np.asarray(sampling_space, dtype=np.float32)
        prediction = kmeans_instance.predict(sampling_space)
        pol = [[list(sampling_space[index]) for index in [i for i, j in enumerate(prediction) if j == k]] for k in range(centers)]
        hull = [shapely.geometry.MultiPoint(pol[i]).convex_hull.exterior._get_coords() for i in range(len(pol))]


