import pandas as pd
import numpy as np
import requests
import os
import json

FILENAME = 'AddressesFull'

def MultipleResultsHandler(response:dict) -> int:
    location = response["summary"]["query"]
    print(f"There were multiple results querying for {location}, please select an option.\n------------------------------------------------------------------------------------")
    for index,item in enumerate(response["results"]):
        item_address = item["address"]["freeformAddress"]
        print(f"{index}) {item_address}")
        
    print("------------------------------------------------------------------------------------")
    selection = -1
    while (selection not in range(response["summary"]["numResults"])):
        selection = input("Please select an option from the ones given above: ")
        try:
            selection = int(selection)
        except ValueError:
            print("Please enter a valid digit from the given options.")
    return int(selection)
    

def PopulateDataframe(df:pd.DataFrame,apiKey:str,pickFirst:bool=False) -> pd.DataFrame:
    assert 'Address' in df.columns, 'Ensure that the Dataframe provided contains a column called "Name".'
    df["Latitude"] = np.nan
    df["Longitude"] = np.nan
    for i in range(len(df)):
        location = df.iloc[i]["Address"]
        if pickFirst:
            response = requests.get(f"https://api.tomtom.com/search/2/geocode/{location}.json?limit=1&key={apiKey}").json()
        else:
            response = requests.get(f"https://api.tomtom.com/search/2/geocode/{location}.json?key={apiKey}").json()
        assert response["summary"]["numResults"] > 0, f"There were no results returned after querying for {location}, are you sure that's a valid location?"
        if (response["summary"]["numResults"] > 1):
            selection = MultipleResultsHandler(response)
            df.at[i,"Latitude"] = response["results"][selection]["position"]["lat"]
            df.at[i,"Longitude"] = response["results"][selection]["position"]["lon"]
        else:
            df.at[i,"Latitude"] = response["results"][0]["position"]["lat"]
            df.at[i,"Longitude"] = response["results"][0]["position"]["lon"]
    # Overwrite old file and return DataFrame
    path = os.path.join(os.getcwd(),'Data',FILENAME+'.csv')
    if os.path.exists(path):
        os.remove(path)
    df.to_csv(path, index='False')
    return df

df = pd.read_csv(os.path.join(os.getcwd(),'Data',FILENAME+'.csv'))
print(df)


with open(os.path.join(os.getcwd(),'Keys.json'), 'r') as f:
    keys = json.load(f)

coords = PopulateDataframe(df, keys['TomTom'])
print(coords)