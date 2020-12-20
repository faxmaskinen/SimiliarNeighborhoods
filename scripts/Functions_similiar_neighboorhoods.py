import pandas as pd # library for data analsysis
import numpy as np
import geocoder # import geocoder
import geopy
from geopy.geocoders import Nominatim
import time
import sys
import requests # library to handle requests
import json # library to handle JSON files
import random # library for random number generation
import time  

def get_coordinates_neighborhoods(df_neighborhoods, city_string, search_col_string):
    # Coordinate arrays
    lat_to_list=np.array([])
    long_to_list=np.array([])
    toolbar_width = 40

    print("")
    print( "progress : Get all Coordinates")

    for i, neigh in enumerate(df_neighborhoods[search_col_string]):
        # initialize your variable to None
        lat_coords =None
        lng_coords =None
        locator = Nominatim(user_agent="myGeocoder")
        count = 0

        # loop until you get the coordinates
        while(lng_coords is None):
            location = locator.geocode('{},'+ city_string.format(neigh))
            try:
                lat_coords = location.latitude
                lng_coords = location.longitude
 
            except:
                lat_coords =None
                lng_coords =None

            if count == 3:  # the limit
                break

            # print(neigh, count)

            count = count + 1

        lat_to_list= np.append(lat_to_list, lat_coords)
        long_to_list= np.append(long_to_list, lng_coords)
        update_progress(round(i/df_neighborhoods.shape[0],1))

    print("Done!")
    return lat_to_list, long_to_list




def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]

    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)



def update_progress(progress): # Thanks Brian (https://stackoverflow.com/questions/3160699/python-progress-bar)
    barLength = 10 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rPercent: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()

def get_weather_data(df_neighborhoods, openweathermap_api_key):
    weather_mean_temp=np.array([])
    weather_most_freq_weather=np.array([])
    weather_2nd_most_freq_weather=np.array([])

    # get coordinates for all neighborhoods
    for lat,lon in df_neighborhoods[['Latitude', 'Longitude']].itertuples(index=False):

        # Get data from api, with coordinates
        url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude={}&appid={}".format(lat, lon, "current,minutely,hourly,alerts", openweathermap_api_key)
        weather_data = requests.get(url).json()
        
        # there is a constraint that MAX 60 api-calls per minutes can be made, thus we make lower number of calls per minute by waiting
        time.sleep(2)
        
        # get weather data for last 5 days and get mean ans most freq
        weather_last_5=[]
        for i in range(0,len(weather_data['daily'])):
            # print(weather_data['daily'][i]['temp']['day'])
            # clean and add data in dataframe
            weather_last_5.append([ round( weather_data['daily'][i]['temp']['day'] -273.15, 2),  weather_data['daily'][i]['weather'][0]['main'] ])
        df_weather_last_5=pd.DataFrame(weather_last_5, columns=['temp','weather'])
        
        # calculate mean temp and most frequent weather, the last 5 days
        mean_temperature = df_weather_last_5['temp'].mean()
        most_freq_weather = df_weather_last_5['weather'].value_counts()[:1].index[0]
        second_most_freq_weather = df_weather_last_5['weather'].value_counts()[:2].index[1]
        # print(second_most_freq_weather)
        
        weather_mean_temp = np.append(weather_mean_temp, mean_temperature)
        weather_most_freq_weather = np.append(weather_most_freq_weather, most_freq_weather)
        weather_2nd_most_freq_weather = np.append(weather_2nd_most_freq_weather, second_most_freq_weather)

    return weather_mean_temp, weather_most_freq_weather, weather_2nd_most_freq_weather