import requests
import pandas as pd

# Input is the download http request, No output variable but file is downloaded as a side effect.
def get_data(url: str):
    response = requests.get(url)
    site_parts = url.split("/")
    filename = site_parts[-1]

    with open(filename, "wb") as f:
        f.write(response.content)
 
    print("Downloaded successfully!")
    return filename

# Input is the file path, Output is the pandas dataframe (can and maybe should another). 
def read_data(file: str):
    return pd.read_excel(file, skiprows=9, sheet_name="Industry Averages") # Hardcoding sheetname is not robust and needs to be optimized.


if __name__ == "__main__":
    main()