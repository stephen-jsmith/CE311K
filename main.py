# Import Statements
import json
import requests
import pandas as pd
import numpy as np
import os

FILENAME = "AddressesTest"

# Open API Key
with open("Keys.json", "r") as data:
    Keys = json.load(data)

# Define API Call Function
def RouteCaller(loc1:str, loc2:str,  key:str=None, units:str='meters', routeType:str='BICYCLE') -> float:
    """ Function that makes a single API call between two distances
    
    # Arguments #
    :arg loc1: Starting location for the route
    :type loc1: str
    :arg loc2: Ending location for the route
    :type loc2: str
    :arg units: Measuring system for the route, metric of imperial
    :type units: str
    :arg routeType: Mode of travel for the route. Default is Bicyle because that's the purpose of this project
    :type routeType: str
    """
    print(f'Getting data for {loc1} to {loc2}')
    # Verify Key exists
    if key == None:
        raise ValueError('No API Key has been passed. Please insert key and try again')
    # Ping the API
    retVal = requests.get(
        f"https://maps.googleapis.com/maps/api/directions/json?destination={loc1}&origin={loc2}&units={units}&mode={routeType}&key={key}").json()
    if 'error_message' in retVal.keys():
        # Error handling
        print(
            f"Error when pinging API, issue: {retVal['error_message']}")
        return np.NaN
    else:
        # Return the route information
        return float(retVal['routes'][0]['legs'][0]['distance']['text'][:-3])

# Define the Distance Matrix
def generateDistanceMatrix(df:pd.DataFrame, key:str) -> np.ndarray:
    """ Takes in a DataFrame, and returns a numpy array

    # Arguments #
    :arg df: all of the addresses in the problem, placed in a pandas DataFrame
    :type df: pd.DataFrame
    :arg key: API key, so that Google knows who is calling
    :type key: str

    # Returns #
    :return distMatrix: A matrix of size NxN, where N is the number of locations in DataFrame df
    :rtype distMatrix: np.ndarray
    """
    # Local array storage
    distDict = {}
    arrays = []

    # Iterate through the DataFrame
    for index1, row1 in df.iterrows():
        distDict[index1] = []
        for index2, row2 in df.iterrows():
            if index1 == index2:
                # If location equals itself then give 0 for distance, no need to ping the API
                distDict[index1].append(0)

            elif index1 != index2:
                # Ping Google's Destination API for route data
                distDict[index1].append(RouteCaller(df.iloc[index1]['Address'], df.iloc[index2]['Address'], key))

    # Process data into arrays, stack, and return
    for key in distDict.keys():
        arrays.append(np.array(distDict[key]))
    distMatrix = np.vstack(arrays)
    return distMatrix


def validateCache(filename:str,df:pd.DataFrame,key:str=None) -> np.ndarray:
    """ Validate and load cached data, to prevent unnecessary API calls

    # Arguments #
    :arg filename: ending of filename to check if it exits. If it doesn't we will end up making it
    :type filename: str
    :arg df: If no cache, need data to pass to route generator
    :type df: pd.DataFrame
    :arg key: If no cache, need key for API call
    :type key: str

    # Returns #
    :return distMatrix: Returns a distmatrix
    :rtype distMatrix: np.ndarray
    """
    # Define where the cache should be
    cache_filename = os.path.splitext(filename)[0] + ".npy"
    # Check for if the parent folder exists, if not make one
    if not os.path.exists(os.path.join(os.path.dirname(__file__),"CachedDistances")):
        os.mkdir(os.path.join(os.path.dirname(__file__),"CachedDistances"))
    # Check if the distance matrix doesn't exist, if so make one
    if not os.path.exists(os.path.join(os.path.dirname(__file__),"CachedDistances",cache_filename)):
        distMatrix = generateDistanceMatrix(df, key)
        np.save(os.path.join(os.path.dirname(__file__),"CachedDistances",cache_filename),distMatrix)
        return distMatrix
    # Since the matrix exists, just load it
    else:
        distMatrix = np.load(os.path.join(os.path.dirname(__file__), "CachedDistances", cache_filename))
        return distMatrix


def main(filename:str,key:str=None):
    """ We put all the work inside this one function, so that at the end of this program we only have to call one function
    
    # Arguments #
    :arg filename: Generic name of the input data file
    :type filename: str
    :arg key: API key needed to call Google Maps if no cached data
    :type key: str
    """
    with open(f"Data/{FILENAME}.csv", "r") as data:
        df = pd.read_csv(data)
        # Make the addresses API friendly
        df = df.replace(' ', '+', regex=True)
    data = validateCache(filename,df,key)
    print(data)

if __name__ == "__main__":
    main(filename=FILENAME, key=Keys['googleMaps'])
