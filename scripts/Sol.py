# Import statements
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd
import requests
import json
import os
import plotly as plt
import plotly.graph_objects as go
import shutil

filename = 'AddressesFull'
MAP_PATH = MAP_PATH = os.path.join(os.getcwd(), "Maps")

with open(os.path.join(os.getcwd(), 'Keys.json')) as f:
    keys = json.load(f)
TomTomKey = keys['TomTom']
MapBoxKey = keys['MapBox']

# -------------------------------------- Interpreting the Solution -------------------------------------- #


def solParser(distMatrix: np.ndarray, filename: str) -> dict:
    """ Read the .sol file and return a much easier to work with dictionary over this xml jargon

    # Arguments #
    :arg distMatrix: 
    :arg filename: Generic name of the input data file
    :type filename: str

    # Returns #
    :ret solution: Usable solution in dictionary form
    :rtype solution: dict
    """
    # Load solution file
    with open(os.path.join(os.getcwd(), 'sol', filename+'.sol'), 'r') as f:
        data = f.read()
    BS_Data = bs(data, 'xml')
    # Get N from distMatrix
    NumElements = len(distMatrix)
    solution = {}
    for i in range(NumElements):
        for j in range(NumElements):
            val = BS_Data.find('variable', {'name': f'i{i}j{j}'})
            if val != None:
                solution[val.get('name')] = val.get('value')
    return solution


def solInterpreter(sol: dict, distMatrix: np.ndarray, filename: str) -> dict:
    """ Takes a solution and outputs the route to the terminal

    # Arguments #
    :arg sol: All of the route variables and associated values for the solution
    :type sol: dict
    :arg distMatrix: Used to get how many locations there are
    :type distMatrix: np.ndarray
    :arg filename: Generic name of the input data file
    :type filename: str

    # Returns #
    :ret routes: The start- and end-points of each route
    :rtype routes: dict
    """
    # Get names of locations
    with open(os.path.join(os.getcwd(), 'Data', filename+'.csv'), "r") as data:
        df = pd.read_csv(data)
    NumElements = len(distMatrix)
    routes = {}
    print('# ---------- Interpreting Solution ---------- #')
    # Get the solution in order, ease of read
    for i in range(NumElements):
        for j in range(NumElements):
            loc = f'i{i}j{j}'
            if loc in sol.keys() and int(sol[loc]) == 1:
                routes[i] = j
    stop = 0
    i = 0

    # Print solution to terminal
    for loc in routes.keys():
        if stop != loc:
            print(
                f'Route contains {df.iloc[routes[stop], 1]} -> {df.iloc[routes[loc], 1]}')
            stop = loc
        elif i != 0:
            print(f'Possible circular route: {loc} -> {stop}, at index {i}')
        i += 1
    # Verify solution is legit
    if i == NumElements:
        print(
            f'Route contains {i} stops out of {NumElements} locations, and is indeed circular!')
    else:
        print(
            f'Route is not circular, as there are {i} stops and {NumElements} locations')
    print(routes)
    return routes


# -------------------------------------- Graphing the Solution -------------------------------------- #

def APIMANAGER(js: str) -> pd.DataFrame:
    jsDump = json.dumps(js)
    jsLoad = json.loads(jsDump)
    points = jsLoad['routes'][0]['legs'][0]['points']
    coords = []
    for item in points:
        coords.append([float(item['longitude']), float(item['latitude'])])
    loc_df = pd.DataFrame(coords, columns=['Longitude', 'Latitude'])
    return loc_df

def routeGenerator(startLat: float, startLon: float, endLat: float, endLon: float, apiKey: str) -> pd.DataFrame:
    tomtomURL = f'https://api.tomtom.com/routing/1/calculateRoute/{startLat},{startLon}:{endLat},{endLon}/json?maxAlternatives=0&routeType=shortest&travelMode=bicycle&key={apiKey}'
    getData = requests.get(tomtomURL)
    while (getData.status_code != 200):
        getData = requests.get(tomtomURL)
    jsonTomTomString = getData.json()
    start = pd.DataFrame({'Latitude':startLat,'Longitude':startLon}, index =[0])
    df = APIMANAGER(jsonTomTomString)
    end = pd.DataFrame({'Latitude':endLat,'Longitude':endLon}, index =[0])
    df = pd.concat([start,df[:],end]).reset_index(drop = True)
    return df


def GenerateMapSolutions(sol: dict, dataframe: pd.DataFrame, apiKey: str) -> dict:
    """Creates a pandas dataframe that represents a solution from the response given by a .sol file

    # Arguments #
    :arg sol: A full circular route
    :type response: dict
    :arg dataframe: A dataframe consisting of at least location Longitude and Latitudes.
    :type dataframe: pd.DataFrame
    :arg apiKey: apiKey for TomTom
    :type apiKey: str

    # Returns #
    :return: A dataframe which represents a series of points of different coordinates and colors that form a route.
    :rtype: pd.DataFrame
    """
    retVal = {}
    for i in sol.keys():
        startLat = dataframe.iloc[i]["Latitude"].item()
        startLon = dataframe.iloc[i]["Longitude"].item()
        endLat = dataframe.iloc[sol[i]]["Latitude"].item()
        endLon = dataframe.iloc[sol[i]]["Longitude"].item()
        print((startLat, startLon), "->", (endLat, endLon))
        retVal[i] = routeGenerator(startLat, startLon, endLat, endLon, apiKey)
    return retVal


def make_map(pathingList:dict, locations:pd.DataFrame, mapboxKey:str, sol:dict) -> None:
    fig = go.Figure(go.Scattergeo())
    # Plot all locations
    lat = locations['Latitude'].values.tolist()
    lon = locations['Longitude'].values.tolist()
    fig.add_trace(go.Scattermapbox(
        lat=lat,
        lon=lon,
        name='Locations'
    ))
    # Plot all routes
    for i in pathingList.keys():
        start = locations.iloc[i]['Name']
        end = locations.iloc[sol[i]]['Name']
        fig.add_trace(go.Scattermapbox(
            mode='lines',
            lat=pathingList[i]['Latitude'].values.tolist(),
            lon=pathingList[i]["Longitude"].values.tolist(),
            name = f'{start} -> {end}'
            )
        )

    # Using Mapbox
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(mapbox_style="light", mapbox_accesstoken=mapboxKey)
    # Display map
    plt.offline.plot(
        fig,
        filename=os.path.join(os.getcwd(), "Maps", f"GeneratedMap.html"),
        auto_open=True,
    )


def ShowMapSolutions(sol: dict, dataframe: pd.DataFrame, TomTomKey: str, MapBoxKey: str):
    """Generates map soutions from a .sol file

    :param sol: A route dictionary
    :type Solutions: dict
    :param dataframe: A dataframe consisting of at least location Longitude and Latitudes.
    :type dataframe: pd.DataFrame
    :param TomTomKey: API key for TomTom, the route provider
    :type TomTomKey: str
    :param MapBoxKey: API key for Plotly Mapbox, the route grapher
    :type MapBoxKey: str
    """
    if os.path.exists(MAP_PATH):
        shutil.rmtree(MAP_PATH)
    os.mkdir(MAP_PATH)
    GeneratedSolution = GenerateMapSolutions(sol, dataframe, TomTomKey)
    make_map(GeneratedSolution, dataframe, MapBoxKey, sol)


if __name__ == "__main__":
    # Load Dist Matrix, Address data
    distMatrix = np.load(os.path.join("CachedDistances", filename + ".npy"))
    df = pd.read_csv(os.path.join(os.getcwd(), 'Data', filename+'.csv'))
    # Pull solution from .sol file
    solution = solParser(distMatrix, filename)
    # Interpret that solution
    sol = solInterpreter(solution, distMatrix, filename)
    # Graph it
    ShowMapSolutions(sol, df, TomTomKey, MapBoxKey)
