# Import Statements
import json
import requests
import pandas as pd
import numpy as np
import os

# -------------------------------------- Creating the Distance Matrix -------------------------------------- #

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
    i = 0
    # Iterate through the DataFrame
    for index1, row1 in df.iterrows():
        distDict[index1] = []
        for index2, row2 in df.iterrows():
            i += 1
            if index1 == index2:
                # If location equals itself then give 0 for distance, no need to ping the API
                distDict[index1].append(0)

            elif index1 != index2:
                # Ping Google's Destination API for route data
                distDict[index1].append(RouteCaller(df.iloc[index1]['Address'], df.iloc[index2]['Address'], key))
    print(f'Successfully made {i} calls to the Google Maps Route API')
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

# -------------------------------------- Defining the Constraints -------------------------------------- #

def generateContraintMatrix(distMatrix:np.ndarray) -> np.ndarray:
    """ Generate the constraint matrix from given distance matrix

    # Arguments #
    :arg distMatrix: Big distance matrix that we calculated in the last step
    :type distMatrix: np.ndarray

    # Returns #
    :return retVal: Combined constraint matrix, with top and bottom halves stacked nicely
    :rtype retVal: np.ndarray
    """
    NumElements = len(distMatrix)
    """
        Generates the top portion of the constraint matrix, a 1 x N matrix of ones for index i in N. Here is an example with N = 3.
        [ 0 0 0 0 0 0 0 0 0 ]        [ 1 1 1 0 0 0 0 0 0 ]
        | 0 0 0 0 0 0 0 0 0 | --->   | 0 0 0 1 1 1 0 0 0 |
        [ 0 0 0 0 0 0 0 0 0 ]        [ 0 0 0 0 0 0 1 1 1 ]
    """
    retArrayTop = np.zeros(shape=(NumElements,NumElements**2))
    for index in range(NumElements):
        retArrayTop[index,index*NumElements:(index+1)*NumElements] = np.ones(shape=(1,NumElements))
    """
        Generates the bottom portion of the constraint matrix, a N x N**2 matrix full of horizontally aligned identity N x N matricies.
        Example with N = 3.
        [ 1 0 0 ]   [ 1 0 0 ]   [ 1 0 0 ]         [ 1 0 0 1 0 0 1 0 0 ]
        | 0 1 0 | + | 0 1 0 | + | 0 1 0 |   --->  | 0 1 0 0 1 0 0 1 0 |
        [ 0 0 1 ]   [ 0 0 1 ]   [ 0 0 1 ]         [ 0 0 1 0 0 1 0 0 1 ]
    """
    individualBottoms = tuple(np.identity(NumElements) for i in range(NumElements))
    retArrayBottom = np.hstack(individualBottoms)
    retVal = np.vstack((retArrayTop,retArrayBottom))
    #retVal = np.vstack((retVal,np.ones(shape=(1,NumElements**2),dtype=np.uint8)))
    return retVal

# -------------------------------------- Getting Ready to Solve -------------------------------------- #

def lpGenerator(distMatrix:np.ndarray, constraintMatrix:np.ndarray,filename:str) -> None:
    """ Writes the lp file for the constraint matrix. LP Files are the way we give the solver our problem.

    # Arguments #
    :arg distMatrix: a distance matrix of size N x N. This contains the necessary objective information
    :type distMatrix: np.ndarray
    :arg constraintMatrix: the constraint matrix with binary variables
    :type constraintMatrix: np.ndarray
    :arg filename: input filename that we will make the associated lp file for
    :type filename: str
    """
    
    # Define where the LP file should be
    lp_filename = os.path.splitext(filename)[0] + ".lp"
    # Check for if the parent folder exists, if not make one
    if not os.path.exists(os.path.join(os.path.dirname(__file__),"LPFiles")):
        os.mkdir(os.path.join(os.path.dirname(__file__),"LPFiles"))
    full_lp_filename = os.path.join(os.path.dirname(__file__),"LPFiles",lp_filename)
    # Delete old lp file of same name
    if os.path.exists(full_lp_filename):
        os.remove(full_lp_filename)

    # Find N
    NumElements = len(distMatrix)

    # Variable Creation
    subtour_vars = {}
    vars_dict = {}
    for i in range(NumElements):
        subtour_vars[i] = f't{i}'
        vars_dict[i] = {}
        for j in range(NumElements):
            vars_dict[i][j] = f'i{i}j{j}'
    # -------------- Objective Writing -------------- #
    costs = []
    for i in vars_dict.keys():
        for j in vars_dict[i].keys():
            cost = distMatrix[i, j]
            if cost != 0.0:
                costs.append(f'{cost} {vars_dict[i][j]}')
                costs.append('+')
    costs.pop()
    # -------------- Constraint Writing -------------- #
    lp_constraints = []
    # Top Third (One route in)
    loc = 0
    for i in vars_dict.keys():
        local = []
        for j in vars_dict[i].keys():
            if i != j:
                if constraintMatrix[i,j+loc] == 1.0:
                    local.append(vars_dict[i][j])
                    local.append(' + ')
        local.pop()
        lp_constraints.append(local)
        loc += NumElements
    # Second Third (One route out)
    loc = 0
    for i in vars_dict.keys():
        local = []
        for j in vars_dict[i].keys():
            if i != j:
                if constraintMatrix[i+NumElements,j*NumElements+loc] == 1.0:
                    local.append(vars_dict[j][i])
                    local.append(' + ')
        local.pop()
        lp_constraints.append(local)
        loc += 1
    # Bottom Third (Subtour elimination)
    subtours =[]
    for i in vars_dict.keys():
        for j in vars_dict[i].keys():
            if i != j:
                if i == 0:
                    # Set i == 0 as the first location visited
                    subtours.append(f'{vars_dict[i][j]} = 1 -> {subtour_vars[i]} = 1')
                else:
                    # Rest of the subtour elimination clause
                    subtours.append(f'{vars_dict[i][j]} = 1 -> {subtour_vars[i]} - {subtour_vars[j]} >= 1')

    # Write the LP file
    with open(full_lp_filename, 'x') as lp:
        # Objective Section
        lp.write('Min \n')
        for eq in costs:
            lp.write(f'{eq} ')
        # Constraint Section
        lp.write('\nsubject to \n')
        for eq in lp_constraints:
            for i in eq:
                lp.write(i)
            lp.write(' = 1 \n')        
        count = 0
        for i in subtours:
            lp.write(f'\nGC{count}: {i}')
            count += 1
        # Define Subtour Variable Bounds
        lp.write('\nbounds \n')
        for i in subtour_vars.keys():
            lp.write(f'0 <= {subtour_vars[i]} <= {NumElements} \n')
        # Define Variable Types
        lp.write('bin \n')
        for i in vars_dict.keys():
            for j in vars_dict[i].keys():
                if i != j:
                    lp.write(f'{vars_dict[i][j]} ')
        lp.write('\nint \n')
        for i in subtour_vars.keys():
            lp.write(f'{subtour_vars[i]} ')
        lp.write('\nEND')