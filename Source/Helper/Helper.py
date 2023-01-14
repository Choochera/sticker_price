import requests
import pandas as pd
import Source.Helper.IHelper as Helper
import simplejson
import yfinance as yf
import yfinance.shared as shared
import json

class helper(Helper.IHelper):
    
    def __init__(self):
        self.processed_symbols: list[str] = []
        self.cikMap = self.__read_cik_map()
        self.symbolMap = {v: k for k, v in self.cikMap.items()}

    
    def retrieve_facts(self, symbol: str) -> dict:
        headers = {'User-Agent': "your@email.com"}
        cik = self.__retrieve_cik(symbol, headers)
        url = "http://127.0.0.1:5000/getFacts/CIK" + cik
        response = requests.get(url, headers=headers)
        try:
            return response.json()
        except simplejson.errors.JSONDecodeError:
            raise Exception('Error retrieving facts')
            
    def retrieve_bulk_facts(self, symbols: list[str]) -> dict:
        facts: dict = dict()
        url = "http://127.0.0.1:5000/getBulkFacts"
        cikList = []
        for symbol in symbols:
            cik = self.__retrieve_cik(symbol)
            cikList.append('CIK' + cik)

        body = {'cikList': cikList}
        response = requests.post(url, json=body)
        for symbolFacts in response.json():
            symbolFacts = symbolFacts[0]
            key = str(symbolFacts['cik'])
            while len(key) != 10:
                key = '0' + key
            facts[self.symbolMap[key]] = symbolFacts

        return facts

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
                    if (stock not in self.processed_symbols):
                        fp.write("%s\n" % stock)

    def download_historical_data(self, stocks: list[str]) -> list:
        h_data: dict = yf.download(stocks, period="15y")
        download_failed_for: list[str] = list(shared._ERRORS.keys())
        self.write_processed_symbols(symbols=download_failed_for)
        stocks = [stock for stock in stocks if stock not in download_failed_for]
        if( len(stocks) == 0 ):
            raise Exception("Download failed for all listed unprocessed symbols")
        return h_data, stocks

    def retrieve_stock_list(self, stocks: list[str]) -> None:
        self.__read_stock_list(stocks)
        self.__read_processed_symbols(self.processed_symbols)
        stocks = [symbol for symbol in stocks if symbol not in self.processed_symbols]
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
    
    def __retrieve_cik_from_sec(self, symbol: str, headers) -> str:
        tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
        tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
        cik = tickers_cik[tickers_cik["ticker"] == symbol]['cik_str']
        cik = cik.reset_index(drop = True)
        try:
            return cik[0]
        except KeyError:
            raise Exception("Could not retrieve cik for " + symbol)

    def __read_cik_map(self) -> dict:
        with open('Service/Data/cikMap.json', 'a+') as file:
            try:
                return json.load(file)
            except json.decoder.JSONDecodeError:
                return dict()

    def __append_to_cik_map(self, symbol: str) -> str:
        headers = {'User-Agent': "your@email.com"}
        cik: str = self.__retrieve_cik_from_sec(symbol, headers)
        self.cikMap[symbol] = cik
        self.symbolMap[cik] = symbol
        with open('Service/Data/cikMap.json', 'w+') as file:
            json.dump(self.cikMap, file) 
        return cik

    def __retrieve_cik(self, symbol: str) -> str:
        try:
            return self.cikMap[symbol]
        except KeyError:
            return self.__append_to_cik_map(symbol)
