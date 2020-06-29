import random
import pandas as pd
from just.simulate.agent.courier import Courier
from just.simulate.agent.customer import Customer
from just.simulate.agent.restaurant import Restaurant
from just.simulate.component.assigner import RandomAssigner, MipAssigner
from just.simulate.geo import random_lat_lng
from just.simulate.metric import *
from just.simulate.session import Session
from just.simulate.simulation import Simulation
from just.simulate.time_dist import TimeDist
from config import *

def query(query_string: str) -> pd.DataFrame:
    """Query."""
    from google.cloud import bigquery
    default_project_id = 'REDACTED_GCP_PROJECT'
    client = bigquery.Client(project=default_project_id)
    job_config = bigquery.QueryJobConfig()
    query_job = client.query(query_string, job_config=job_config)
    return query_job.result().to_dataframe()

'''
dfrestaurants = query(qrestaurants)
restaurants = query(qrestaurants).values.tolist()
restaurants = [Restaurant(id = restaurants[i][0], lat = restaurants[i][1], lng = restaurants[i][2]) for i in range(len(restaurants))]
lat = dfrestaurants['address_latitude'].mean()
lng = dfrestaurants['address_longitude'].mean()
'''
num_customers = 279
radius = 500  # meters
num_couriers = 5
num_restaurants = 5
time_dist = TimeDist('norm', 16.0, 1.0, unit='hours')



restaurants = list([])
for i in range(num_restaurants):
    lat, lng = random_lat_lng(51.5076, -0.0994, radius)
    restaurants.append(Restaurant(f'Restaurant {i}', lat, lng))

customers = list([])
for j in range(num_customers):
    lat, lng = random_lat_lng(lat,lng, radius)
    customers.append(Customer(f'Customer {j}', lat, lng))

sessions = list([])
for customer in customers:
    restaurant = random.choice(restaurants)
    timestamp = time_dist.random_variate()
    sessions.append(Session(customer.id, restaurant.id, timestamp))

couriers = list([])
for k in range(num_couriers):
    lat, lng = random_lat_lng(lat, lng, radius)
    couriers.append(Courier(f'Courier {k}', lat, lng))
    
    
#assigner = RandomAssigner()
assigner = MipAssigner()

metrics = [
    DeliveryTime(),
    NumberOfOrdersDelivered(),
    #CourierUtilisation(),
    OrdersDeliveredPerHour(),
    ReadyToDoorTime(),
    TopTwoRestaurantsByOrderVolume()
]    


simulation = Simulation(
    restaurants=restaurants,
    customers=customers,
    sessions=sessions,
    couriers=couriers,
    assigner=assigner,
    metrics=metrics
)



results = simulation.run(verbose=1)

results