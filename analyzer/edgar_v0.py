import pandas as pd
import requests


def main():
    headers = {"User-Agent": "marcos@fundamentaltech.com"} # This is "sensitive" info, store it in a environment variable
    ticker = input("Ticker: ")

    # Get CIK number
    cik = get_cik(ticker, headers)
    
    # Get data submissions
    data = get_submission_data_for_ticker(cik, headers, only_filings_df=True)
    print(data)

    # Get 10-K, 10-Q
    #data = get_filtered_filings(cik, ten_k=False, just_accession_numbers=True, headers=headers)
    #print(data)


# Input: ticker symbol, output: CIK number 
def get_cik(ticker, headers) -> str:
    headers = headers # Not robust!
    ticker = ticker.upper().replace(".", "-")
    ticker_json = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers).json()

    for company in ticker_json.values():
        if company["ticker"] == ticker:
            cik = str(company["cik_str"]).zfill(10)
            return cik
    raise ValueError(f"Ticker {ticker} not found in SEC database")


# Input: CIK number, output: submission data
def get_submission_data_for_ticker(cik, headers, only_filings_df=False):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    company_json = requests.get(url, headers=headers).json()
    if only_filings_df:
        return pd.DataFrame(company_json["filings"]["recent"])
    return company_json


# Input: CIK number, output: filtered filings (10-K or 10-Q)
# Customize!!
def get_filtered_filings(cik, headers, ten_k=True, ten_q=False, just_accession_numbers=False):
    company_filings_df = get_submission_data_for_ticker(cik, only_filings_df=True, headers=headers)
    if ten_k:
        df = company_filings_df[company_filings_df["form"] == "10-K"]
    else:
        df = company_filings_df[company_filings_df["form"] == "10-Q"]
    if just_accession_numbers:
        df = df.set_index("reportDate")
        accession_df = df["accessionNumber"]
        return accession_df
    else:
        return df
    

def get_facts(cik, headers):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    company_facts = requests.get(url, headers=headers).json()
    return company_facts


def facts_DF(cik, headers):
    facts = get_facts(cik, headers)
    us_gaap_data = facts["facts"]["us-gaap"]
    df_data = []
    for fact, details in us_gaap_data.items():
        for unit in details["units"]:
            for item in details["units"][unit]:
                row = item.copy()
                row["fact"] = fact
                df_data.append(row)
                               
    df = pd.DataFrame(df_data)
    df["end"] = pd.to_datetime(df["end"])
    df["start"] = pd.to_datetime(df["start"])
    df = df.drop_duplicates(subset=["fact", "end", "val"])
    df.set_index("end", inplace=True)
    labels_dict = {fact: details["label"] for fact, details in us_gaap_data.items()}
    return df, labels_dict


def annual_facts(cik, headers):
    accession_nums = get_filtered_filings(
        cik, headers, ten_k=True, just_accession_numbers=True
    )
    df, label_dict = facts_DF(cik, headers)
    ten_k = df[df["accn"].isin(accession_nums)]
    ten_k = ten_k[ten_k.index.isin(accession_nums.index)]
    pivot = ten_k.pivot_table(values="val", columns="fact", index="end")
    pivot.rename(columns=label_dict, inplace=True)
    return pivot.T


def get_quarterly_facts(cik, headers):
    accession_nums = get_filtered_filings(
        cik, headers, ten_k=False, just_accession_numbers=True
    )
    df, label_dict = facts_DF(cik, headers)
    ten_q = df[df["accn"].isin(accession_nums)]
    ten_q = ten_q[ten_q.index.isin(accession_nums.index)]
    ten_q = ten_q[ten_q.index.isin(accession_nums.index)].reset_index(drop=False)
    ten_q = ten_q.drop_duplicates(subset=["fact", "end"], keep="last")
    pivot = ten_q.pivot_table(values="val", columns="fact", index="end")
    pivot.rename(columns=label_dict, inplace=True)
    return pivot.T


if __name__ == "__main__":
    main()