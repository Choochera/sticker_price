from datetime import datetime
import requests
import pandas as pd
import Source.Helper.IHelper as Helper
import simplejson
import yfinance as yf
import yfinance.shared as shared
import json
import os
import Source.constants as const
import Source.Exceptions.DataRetrievalException as DRE
import Source.Exceptions.DisqualifyingDataException as DDE
import asyncio


class helper(Helper.IHelper):

    def __init__(self):
        self.processed_symbols: list[str] = []
        self.cikMap = self.__read_cik_map()
        self.symbolMap = {v: k for k, v in self.cikMap.items()}

    def days_between(self, d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    def retrieve_facts(self, symbol: str) -> dict:
        headers = {'User-Agent': const.HELPER_USER_AGENT}
        try:
            cik = self.__retrieve_cik(symbol)
        except DRE.DataRetrievalException:
            raise DRE.DataRetrievalException(const.LOWER_CIK)
        url = const.SERVICE_GET_FACTS_URL % cik
        response = requests.get(url, headers=headers)
        try:
            return response.json()[0][0]
        except simplejson.errors.JSONDecodeError:
            raise DRE.DataRetrievalException(const.FACTS)

    def add_padding_to_collection(self, dict_list: dict, padel: str) -> None:
        lmax = 0
        for lname in dict_list.keys():
            lmax = max(lmax, len(dict_list[lname]))
        for lname in dict_list.keys():
            ll = len(dict_list[lname])
            if ll < lmax:
                dict_list[lname] += [padel] * (lmax - ll)
        return dict_list

    def write_error_file(
        self,
        symbol: str,
        messageType: str,
        exceptionType: str,
        facts: dict
    ) -> None:
        with open(
            'Errors/%s_%s_%s.json' % (exceptionType, messageType, symbol),
            const.WRITE
        ) as file:
            json.dump(facts, file)
            raise DRE.DataRetrievalException(
                messageType
            )

    def write_processed_symbols(
            self,
            symbol: str = None,
            symbols: list[str] = None) -> None:
        with open(const.PROCESSED_SYMBOLS_FILE, const.APPEND) as fp:
            if (symbol is not None):
                fp.write(const.SYMBOL_LINE % symbol)
            if (symbols is not None):
                for stock in symbols:
                    if (stock not in self.processed_symbols):
                        fp.write(const.SYMBOL_LINE % stock)

    def retrieve_stock_list(self, stocks: list[str]) -> None:
        self.__read_stock_list(stocks)
        self.__read_processed_symbols(self.processed_symbols)
        stocks = [
            symbol for symbol in stocks if symbol not in self.processed_symbols
            ]
        if (len(stocks) == 0):
            raise DDE.DisqualifyingDataException(type=const.ALL_PROCESSED)

    def download_historical_data(
            self,
            stocks: list[str]) -> tuple[dict, list[str]]:
        h_data: dict = yf.download(stocks, period="15y")
        download_failed: list[str] = list(shared._ERRORS.keys())
        self.write_processed_symbols(symbols=download_failed)
        stocks = [stock for stock in stocks if stock not in download_failed]
        if (len(stocks) == 0):
            raise DRE.DataRetrievalException(const.H_DATA)
        return h_data, stocks

    async def retrieve_bulk_facts(
            self,
            symbols: list[str],
            loop: asyncio.AbstractEventLoop) -> dict:
        facts: dict = dict()
        tasks = []
        for i in range(0, len(symbols), 5):
            stocks = symbols[i:i+10]
            tasks.append(loop.create_task(
                self.__call_service_for_facts(stocks, facts))
                )
        await asyncio.wait(tasks)
        return facts

    async def __call_service_for_facts(
            self,
            stocks: list[str],
            facts: dict) -> None:
        cikList = []
        url = const.SERVICE_GET_BULK_FACTS_URL
        for symbol in stocks:
            try:
                cik = self.__retrieve_cik(symbol)
                cikList.append(const.UPPER_CIK + cik)
            except DRE.DataRetrievalException:
                pass
        body = {const.CIK_LIST: cikList}
        response = requests.post(url, json=body)
        for symbolFacts in response.json():
            symbolFacts = symbolFacts[0]
            key = str(symbolFacts[const.LOWER_CIK])
            while len(key) != 10:
                key = const.ZERO + key
            facts[self.symbolMap[key]] = symbolFacts

    def __read_stock_list(self, stocks: list[str]) -> None:
        try:
            with open(const.STOCKLIST_FILE) as f:
                lines = f.readlines()
                for line in lines:
                    stock = line.split('\n')[0]
                    if (len(stock) > 0):
                        if (stock.isalpha()):
                            stocks.append(stock)
        except FileNotFoundError:
            with open(const.STOCKLIST_FILE, const.WRITE) as f:
                None

    def __read_processed_symbols(self, processedSymbols: list[str]) -> None:
        try:
            with open(const.PROCESSED_SYMBOLS_FILE) as f:
                lines = f.readlines()
                for line in lines:
                    stock = line.split('\n')[0]
                    if (len(stock) > 0):
                        processedSymbols.append(stock)
        except FileNotFoundError:
            with open(const.PROCESSED_SYMBOLS_FILE, const.WRITE) as fp:
                None

    def __retrieve_cik_from_sec(self, symbol: str, headers) -> str:
        tickers_cik = requests.get(const.SEC_CIK_URL, headers=headers)
        data = pd.json_normalize(tickers_cik.json(), max_level=0).values[0]
        tickers_cik = pd.json_normalize(data)
        data = tickers_cik[const.CIK_STR].astype(str).str.zfill(10)
        tickers_cik[const.CIK_STR] = data
        cik = tickers_cik[tickers_cik[const.TICKER] == symbol][const.CIK_STR]
        cik = cik.reset_index(drop=True)
        try:
            return cik[0]
        except KeyError:
            raise DRE.DataRetrievalException(const.LOWER_CIK)

    def __read_cik_map(self) -> dict:
        if not os.path.exists(const.DATA_PATH):
            os.makedirs(const.DATA_PATH)
        with open(const.CIKMAP_PATH, const.APPEND_PLUS) as file:
            try:
                return json.load(file)
            except json.decoder.JSONDecodeError:
                return dict()

    def __append_to_cik_map(self, symbol: str) -> str:
        headers = {'User-Agent': const.HELPER_USER_AGENT}
        cik: str = self.__retrieve_cik_from_sec(symbol, headers)
        self.cikMap[symbol] = cik
        self.symbolMap[cik] = symbol
        with open(const.CIKMAP_PATH, const.WRITE_PLUS) as file:
            json.dump(self.cikMap, file)
        return cik

    def __retrieve_cik(self, symbol: str) -> str:
        try:
            return self.cikMap[symbol]
        except KeyError:
            return self.__append_to_cik_map(symbol)
