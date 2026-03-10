import requests
import pandas as pd

class Stock:
    def __init__(self, ticker):
        if not ticker:
            raise ValueError("Ticker cannot be empty")
        
        self.ticker = ticker.upper().replace(".", "-")
        self.headers = {"User-Agent": "marcos@gmail.com"} # Not robust, change later.
        self.cik = self.get_cik()
        self._facts_df = None           # cache
        self._facts_df_gaap = None      # cache
        self._label_dict_gaap = None    # cache
        self._submission_data = None    # cache
        self._accession_nums = None     # cache            

    def get_cik(self):
        ticker_json = requests.get("https://www.sec.gov/files/company_tickers.json", headers=self.headers).json()

        for company in ticker_json.values():
            if company["ticker"] == self.ticker:
                cik = str(company["cik_str"]).zfill(10)
                return cik
        raise ValueError(f"Ticker {self.ticker} not found in SEC database")
    
    def get_submission_data(self, only_filings_df=False):
        if self._submission_data is None:
            self._submission_data = self._get_submission_data(only_filings_df=only_filings_df)
        return self._submission_data

    def get_filtered_filings(self, ten_k=True, ten_q=False, just_accession_numbers=False):
        company_filings_df = self.get_submission_data(only_filings_df=True)
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

    def get_facts(self):
        if self._facts_df is None:
            self._facts_df = self._get_facts()
        return self._facts_df
    
    def get_facts_gaap(self):
        if self._facts_df_gaap is None:
            self._facts_df_gaap, self._label_dict_gaap = self._get_facts_gaap()
        return self._facts_df_gaap, self._label_dict_gaap
        
    def get_annual_facts(self):
        accession_nums = self.get_filtered_filings(
            ten_k=True, just_accession_numbers=True
        )
        df, label_dict = self.get_facts_gaap(self.cik, self.headers)
        ten_k = df[df["accn"].isin(accession_nums)]
        selected_ends = pd.to_datetime(accession_nums.index)
        ten_k = ten_k[ten_k.index.isin(selected_ends)]
        pivot = ten_k.pivot_table(values="val", columns="fact", index="end")
        pivot.rename(columns=label_dict, inplace=True)
        return pivot.T
    
    def get_quarterly_facts(self):
        accession_nums = self.get_filtered_filings(
            ten_k=False, just_accession_numbers=True
        )
        df, label_dict = self.get_facts_gaap()
        ten_q = df[df["accn"].isin(accession_nums)]
        selected_ends = pd.to_datetime(accession_nums.index)
        ten_q = ten_q[ten_q.index.isin(selected_ends)].reset_index(drop=False)
        ten_q = ten_q.drop_duplicates(subset=["fact", "end"], keep="last")
        pivot = ten_q.pivot_table(values="val", columns="fact", index="end")
        pivot.rename(columns=label_dict, inplace=True)
        return pivot.T

    ##################################################################################
    ### Internal methods (not for external use, but can be used for caching, etc.) ###
    ##################################################################################

    # Facts dataframe with caching (this is the actual implementation)

    def _get_facts(self):
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.cik}.json"
        company_facts = requests.get(url, headers=self.headers).json()
        return company_facts

    def _get_facts_gaap(self):
        facts = self.get_facts()
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

    def _get_submission_data(self, only_filings_df=False):
        url = f"https://data.sec.gov/submissions/CIK{self.cik}.json"
        company_json = requests.get(url, headers=self.headers).json()
        if only_filings_df:
            return pd.DataFrame(company_json["filings"]["recent"])
        return company_json
















    # Data retrieval methods

    def get_10k(self):
        ... # This is a bit hacky, but it works for now. Refactor later.

    def get_10q(self):
        ... # This is a bit hacky, but it works for now. Refactor later.

    def income_statement(self):
        ... # return income statement as a dataframe, with years as index and line items as columns. Refactor later.

    def balance_sheet(self):
        ... # return balance sheet as a dataframe, with years as index and line items as columns. Refactor later.
    
    def cash_flow_statement(self):
        ... # return cash flow statement as a dataframe, with years as index and line items as columns. Refactor later.