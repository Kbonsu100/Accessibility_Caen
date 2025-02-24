# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 16:03:49 2024

@author: kbons
"""

#java -Xmx48G -jar otp-1.5.0-shaded.jar --build C:/Users/kbons/accessibility/Orleans_2 --inMemory --analyst 

import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from datetime import datetime
import os

# Function to connect to OTP and get isochrones
def get_isochrone(base_url, lat, lon, modes, date_time, cutoff_minutes, max_walk_distance=None):
    params = {
        'fromPlace': f'{lat},{lon}',
        'mode': ','.join(modes),
        'date': date_time.strftime('%Y-%m-%d'),
        'time': date_time.strftime('%H:%M:%S'),
        'cutoffSec': [m * 60 for m in cutoff_minutes]
    }
    
    if max_walk_distance:
        params['maxWalkDistance'] = max_walk_distance

    response = requests.get(f'{base_url}/otp/routers/default/isochrone', params=params)
    
    if response.status_code == 200:
        return response.json().get('features', [])
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []

# Set base URL for OTP API
otp_base_url = 'http://localhost:8080'

# Load the grid center data
centres = pd.read_csv('data/Caen_centers.csv', sep=',')

# Function to process isochrones and save to file
def process_and_save_isochrone(features, directory, filename, id_column):
    if features:
        try:
            # Attempt to create GeoDataFrame and extract properties
            gdf = gpd.GeoDataFrame.from_features(features)
            if 'properties' in gdf.columns:
                gdf['minutes'] = gdf['properties'].apply(lambda x: x.get('time', 0) / 60)
            else:
                # Fallback if 'properties' is missing
                print(f"No 'properties' found for ID: {id_column}. Using default values.")
                gdf['minutes'] = 0  # Or any other default/fallback logic you prefer
            
            os.makedirs(directory, exist_ok=True)
            gdf.to_file(f'{directory}/{filename}_{id_column}.shp')
        except KeyError as e:
            print(f"KeyError: {e} for ID: {id_column}. Full feature: {features}")

# Transit Isochrones
for i, row in centres.iterrows():
    features = get_isochrone(
        base_url=otp_base_url,
        lat=row['Y'],
        lon=row['X'],
        modes=['WALK', 'TRANSIT'],
        date_time=datetime(2024, 10, 21, 8, 30),
        cutoff_minutes=[15, 30, 45, 60, 75, 90],
        max_walk_distance=1000
    )
    process_and_save_isochrone(features, './transit', 't', row["ID"])

# Bicycle Isochrones
for i, row in centres.iterrows():
    features = get_isochrone(
        base_url=otp_base_url,
        lat=row['Y'],
        lon=row['X'],
        modes=['BICYCLE'],
       date_time=datetime(2024, 10, 21, 8, 30),
       cutoff_minutes=[15, 30, 45, 60, 75, 90],
    )
    process_and_save_isochrone(features, './bicycle', 'b', row["ID"])

# Car Isochrones 
for i, row in centres.iterrows():
    features = get_isochrone(
        base_url=otp_base_url,
        lat=row['Y'],
        lon=row['X'],
        modes=['CAR'],
        date_time=datetime(2024, 10, 21, 8, 30),
        cutoff_minutes=[15, 30, 45, 60, 75, 90],
     )
    process_and_save_isochrone(features, './car', 'c', row["ID"])
