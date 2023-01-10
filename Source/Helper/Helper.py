import requests
import pandas as pd
import lxml.html as lh
import Helper.IHelper
import simplejson
import yfinance as yf
import yfinance.shared as shared

class helper(Helper.IHelper.IHelper):
    
    def __init__(self):
        None

    def send_SEC_api_request(self, symbol: str, element: str) -> requests.Response:
        headers = {'User-Agent': "your@email.com"}
        tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
        tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
        cik = tickers_cik[tickers_cik["ticker"] == symbol]['cik_str']
        cik = cik.reset_index(drop = True)
        url = "https://data.sec.gov/api/xbrl/companyconcept/CIK" + cik[0] + "/us-gaap/" + element + ".json"
        response = requests.get(url, headers=headers)
        return response

    def retrieve_facts(self, symbol: str) -> dict:
        headers = {'User-Agent': "your@email.com"}
        tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
        tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
        cik = tickers_cik[tickers_cik["ticker"] == symbol]['cik_str']
        cik = cik.reset_index(drop = True)
        try:
            url = "https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik[0] + ".json"
        except KeyError:
            raise Exception('Error retrieving cik data')
        response = requests.get(url, headers=headers)
        try:
            return response.json()
        except simplejson.errors.JSONDecodeError:
            raise Exception('Error retrieving facts')

    def retrieve_fy_growth_estimate(self, symbol: str) -> float:
        url = "https://www.zacks.com/stock/quote/" + symbol + "/detailed-estimates"
        try:
            page = requests.get(url, headers = {'User-Agent' : '008'})
            doc = lh.fromstring(page.content)
        except requests.exceptions.HTTPError as hError:
            raise Exception(str("Http Error:", hError))
        except requests.exceptions.ConnectionError as cError:
            raise Exception(str("Error Connecting:", cError))
        except requests.exceptions.Timeout as tError:
            raise Exception(str("Timeout Error:", tError))
        except requests.exceptions.RequestException as rError:
            raise Exception(str("Other Error:", rError))

        td_elements = doc.xpath('//td')

        for i in range(len(td_elements)):
            if(td_elements[i].text_content() == 'Next 5 Years'):
                return td_elements[i + 1].text_content() 
        
        return -1

    def add_padding_to_collection(self, dict_list: dict, padel: str) -> None:
        lmax = 0
        for lname in dict_list.keys():
            lmax = max(lmax, len(dict_list[lname]))
        for lname in dict_list.keys():
            ll = len(dict_list[lname])
            if  ll < lmax:
                dict_list[lname] += [padel] * (lmax - ll)
        return dict_list

    def write_processed_symbols(self, symbol: str = None, symbols: list[str] = None) -> None:
        with open(r'processedSymbols.txt', 'a') as fp:
            if (symbol != None):
                fp.write("%s\n" % symbol)
            if (symbols != None):
                for stock in symbols:
                    fp.write("%s\n" % stock)

    def download_historical_data(self, stocks: list[str]) -> list:
        h_data: dict = yf.download(stocks, period="10y")
        download_failed_for: list[str] = list(shared._ERRORS.keys())
        self.write_processed_symbols(symbols=download_failed_for)
        stocks = [stock for stock in stocks if stock not in download_failed_for]
        if( len(stocks) == 0 ):
            raise Exception("Download failed for all listed unprocessed symbols")
        return h_data, stocks

    def retrieve_stock_list(self, stocks: list[str]) -> None:
        processedSymbols: list[str] = []
        self.__read_stock_list(stocks)
        self.__read_processed_symbols(processedSymbols)
        stocks = [symbol for symbol in stocks if symbol not in processedSymbols]
        if( len(stocks) == 0 ):
            raise Exception("All symbols in list have been processed")

    def __read_stock_list(self, stocks: list[str]) -> None:
        try:
            with open('stockList.txt') as f:
                lines = f.readlines()
                for line in lines:
                    stock = line.split('\n')[0]
                    if(len(stock) > 0):
                        stocks.append(stock)
        except FileNotFoundError:
            with open('stockList.txt', 'w') as f:
                    None

    def __read_processed_symbols(self, processedSymbols: list[str]) -> None:
        try:
            with open('processedSymbols.txt') as f:
                    lines = f.readlines()
                    for line in lines:
                        stock = line.split('\n')[0]
                        if(len(stock) > 0):
                            processedSymbols.append(stock)
        except FileNotFoundError:
            with open(r'processedSymbols.txt', 'w') as fp:
                None        
