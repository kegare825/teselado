# -*- coding: utf-8 -*-
"""
Created on Sun Jul 12 20:05:44 2020

@author: Carlos Moreno Morera & Aarón González
"""

import numpy as np

class K_Means:
    
    """
    Class which implements K-Means algorithm with the required distance.
    
    Attributes
    ----------
    __k : int
        Number of clusters.
    __tol : float
        Tolerance.
    __max_iter : int
        Maximum number of iterations.
    __centroids : dict
        Resulting centroids after executing K-Means algorithm.
    __metric : function
        Metric used in the algorithm.
        
    """
    
    def __init__(self, k=3, tol=0.001, max_iter=3000, 
                 metric = lambda c, e : 1.3*np.linalg.norm(e - c)):
        """
        Class constructor
        
        Parameters
        ----------
        k : int (optional)
            Number of clusters. The default value is 3.
        tol : float (optional)
            Tolerance. The default value is 0.001.
        max_iter : int (optional)
            Maximum number of iterations. The default value is 3000.
        metric : function (optional)
            Metric used in the algorithm. The default value is the lambda
            function lambda c, e : 1.3*np.linalg.norm(e - c).
            
        Returns
        -------
        Constructed K_Means class.
        
        """
        self.__k = k
        self.__tol = tol
        self.__max_iter = max_iter
        self.__centroids = {}
        self.__metric = metric
    
    def fit(self, data):
        """
        Computes k-means clustering.
        
        Parameters
        ----------
        data : np.ndarray
            Training instances to cluster.
        
        Returns
        -------
        None.
        
        """
        optimized = False
        i = 0
        
        while not(optimized) and i < self.__k:
            self.__centroids[i] = data[i]
        
        for i in range(self.__max_iter):
            classifications = {}
        
            for j in range(self.__k):
                classifications[j] = []
        
            for featureset in data:
                distances = [self.__metric(self.__centroids[centroid], featureset) 
                             for centroid in self.__centroids]
        
                classification = distances.index(min(distances))
                classifications[classification].append(featureset)
        
            prev_centroids = self.__centroids.copy()
        
            for classification in classifications:
                self.__centroids[classification] = np.average(
                    classifications[classification],axis=0)
        
            optimized = True
        
            for c in self.__centroids:
                original_centroid = prev_centroids[c]
                current_centroid = self.__centroids[c]
                if (np.sum((current_centroid-original_centroid)/original_centroid*100.0) 
                    > self.__tol):
                    optimized = False
        
            i += 1
    
    def predict(self,data):
        """
        TO FILL

        Parameters
        ----------
        data : np.array
            Assigns clusters to data.

        Returns
        -------
        classification : np.array
            Vector of labels assigning clusters.

        """
        distances = [np.linalg.norm(data-self.__centroids[centroid]) 
                     for centroid in self.__centroids]
        classification = distances.index(min(distances))
        return classification
    