from analyzer import Stock
import pandas as pd


def main():
    stock = Stock("MSFT")
    data = stock.get_annual_facts()


#    stock = "AAPL"
#    cik = get_cik(stock, headers={"User-Agent": "marcos@gmail.com"})
#    df, labels = facts_DF(cik, headers={"User-Agent": "marcos@gmail.com"})

    print(data)


if __name__ == "__main__":
    main()