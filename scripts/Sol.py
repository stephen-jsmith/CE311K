# Import statements
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd

# -------------------------------------- Interpreting the Solution -------------------------------------- #

def solParser(distMatrix:np.ndarray, filename:str) -> dict:
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
    with open(f'sol/{filename}.sol', 'r') as f:
        data = f.read()
    BS_Data = bs(data, 'xml')
    # Get N from distMatrix
    NumElements = len(distMatrix)
    solution = {}
    for i in range(NumElements):
        for j in range(NumElements):
            val = BS_Data.find('variable', {'name':f'i{i}j{j}'})
            if val != None:
                solution[val.get('name')] = val.get('value')
    return solution

def solInterpreter(sol:dict, distMatrix:np.ndarray, filename:str) -> None:
    """ Takes a solution and outputs the route to the terminal

    # Arguments #
    :arg sol: All of the route variables and associated values for the solution
    :type sol: dict
    :arg distMatrix: Used to get how many locations there are
    :type distMatrix: np.ndarray
    :arg filename: Generic name of the input data file
    :type filename: str
    """
    # Get names of locations
    with open(f"Data/{filename}.csv", "r") as data:
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
            print(f'Route contains {df.iloc[routes[stop], 0]} -> {df.iloc[routes[loc], 0]}')
            stop = loc
        elif i != 0:
            print(f'Possible circular route: {loc} -> {stop}, at index {i}')
        i += 1
    # Verify solution is legit
    if i == NumElements:
        print(f'Route contains {i} stops out of {NumElements} locations, and is indeed circular!')
    else:
        print(f'Route is not circular, as there are {i} stops and {NumElements} locations')