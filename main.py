from scripts.Modeler import *
from scripts.Sol import *

FILENAME = "AddressesFull"

# Open API Key
with open("Keys.json", "r") as data:
    Keys = json.load(data)

# ------------------------------------------ Solve or Interpret Functions ------------------------------------------- #

def solve(filename:str,key:str=None) -> None:
    """ Generate the model and associated LP File for a data set

    # Arguments #
    :arg filename: Generic name of the input data file
    :type filename: str
    :arg key: API key needed to call Google Maps if no cached data
    :type key: str
    """
    # Open the data, put it in Pandas
    with open(f"Data/{filename}.csv", "r") as data:
        df = pd.read_csv(data)
        # Make the addresses API friendly
        df = df.replace(' ', '+', regex=True)
    # Get distance matrix
    distMatrix = validateCache(filename,df,key)
    constMatrix = generateContraintMatrix(distMatrix)
    # Write LP File for solve
    lpGenerator(distMatrix, constMatrix, filename)

def interpret(filename:str) -> None:
    """ Reads a .sol file and puts a readable output to the terminal

    # Arguments #
    :arg filename: Generic name of the input data file
    :type filename: str
    """
    # Load Dist Matrix
    distMatrix = np.load(os.path.join("CachedDistances", filename + ".npy"))
    # Pull solution from .sol file
    solution = solParser(distMatrix, filename)
    # Interpret that solution
    solInterpreter(solution, distMatrix, filename)

# -------------------------------------------------- Define Main ---------------------------------------------------- #

def main(filename:str,key:str=None) -> None:
    """ We put all the work inside this one function, so that at the end of this program we only have to call one function

    # Arguments #
    :arg filename: Generic name of the input data file
    :type filename: str
    :arg key: API key needed to call Google Maps if no cached data
    :type key: str
    """
    val = input(f'Solve or Interpret {filename}? Press 0 to generate LP File, or 1 for Interpret: ')
    choice = int(val)
    if choice != 1 and choice != 0:
        val = input(f'Error! Unknown charachter "{choice}". Pleae press 0 to generate LP File, or 1 for Interpret: ')
        choice = int(val)
    if choice == 0:
        solve(filename, key)
    if choice == 1:
        interpret(filename)

if __name__ == "__main__":
    main(filename=FILENAME, key=Keys['googleMaps'])