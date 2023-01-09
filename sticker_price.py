import pandas as pd
import threading
import yfinance as yf
import time
import sys
import Source.ComponentFactory

MAX_NUMBER_OF_THREADS=10
lock = threading.Lock()

# Rule 1 equation application. Uses PE and equity growth to predict what price will be based on required rate of return and number of years.
def checkIsOnSale(symbol: str, priceData: dict, stocksOnSale: list[str]) -> None:
    stock = yf.Ticker(symbol)
    price = stock.history(period='1d')['Close'][0]
    sale_prices = priceData['sale_price']
    if( (sale_prices[0] > 0 and sale_prices[1] > 0 and sale_prices[2] > 0) and (price < sale_prices[0] or price < sale_prices[1] or price < sale_prices[2])):
        print( symbol + " is on sale")
        stocksOnSale.append(symbol)
        pad_dict_list(priceData, '')
        df = pd.DataFrame.from_dict(priceData)
        df.to_csv('Output/' + symbol + '.csv', index=False)
    else:
        print( symbol + " is not on sale")

def pad_dict_list(dict_list, padel):
    lmax = 0
    for lname in dict_list.keys():
        lmax = max(lmax, len(dict_list[lname]))
    for lname in dict_list.keys():
        ll = len(dict_list[lname])
        if  ll < lmax:
            dict_list[lname] += [padel] * (lmax - ll)
    return dict_list

def retrieve_stock_list(stocks: list[str]) -> None:
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

def retrieve_processed_symbols(processedSymbols: list[str]) -> None:
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

def write_to_processed_symbols(symbol: str) -> None:
    with lock:
        with open(r'processedSymbols.txt', 'a') as fp:
            fp.write("%s\n" % symbol)

def download_historical_data(symbols: list[str]) -> dict:
        return yf.download(symbols, period="10y")

class generatorThread (threading.Thread):
   def __init__(self, threadID, name, counter, symbols: list[str], h_data: dict):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      self.symbols = symbols
      self.h_data = h_data
   def run(self):
        for symbol in self.symbols:
            try:
                calculator = Source.ComponentFactory.ComponentFactory.getDataCalculatorObject(symbol, self.h_data)
                checkIsOnSale(symbol, calculator.calculate_sticker_price_data(), stocksOnSale)
            except Exception as e: 
                print("Could not retrieve data for " + symbol, e)
            write_to_processed_symbols(symbol)

if __name__ == "__main__":

    stocksOnSale: list[str]= []
    processedSymbols: list[str] = []
    stocks = sys.argv[1:]

    startTime = time.time()

    if( len(stocks) == 0 ):
        retrieve_stock_list(stocks)
        retrieve_processed_symbols(processedSymbols)
        stocks = [symbol for symbol in stocks if symbol not in processedSymbols]

    if( len(stocks) == 0 ):
        raise Exception("All symbols in list have been processed")

    h_data: dict = download_historical_data(stocks)

    if( len(stocks)%MAX_NUMBER_OF_THREADS == 0 ):
        step = int(len(stocks)/MAX_NUMBER_OF_THREADS)
    else:
        step = int(len(stocks)/MAX_NUMBER_OF_THREADS) + 1

    threads = []
    stock_groups = []
    for i in range(0, len(stocks), step):
        stock_groups.append(stocks[i:i+step])
    for i in range(len(stock_groups)):
        threads.append(generatorThread(i + 1, "thread_" + str(i + 1), i+1, symbols = stock_groups[i], h_data=h_data))
        threads[int(i)].start()
    for t in threads:
        t.join()
    del(threads)

    end = time.time()
    
    print("Sticker Price Analysis Complete\nElapsed time: %2d minutes, %2d seconds\n" % ((end - startTime)/60, (end - startTime)%60))
    print(stocksOnSale)