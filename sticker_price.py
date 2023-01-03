import Data_Calculator
import pandas as pd
import threading
import yfinance as yf
import time
import sys

MAX_NUMBER_OF_THREADS=10
calculator: Data_Calculator.dataCalculator = Data_Calculator.dataCalculator()

# Rule 1 equation application. Uses PE and equity growth to predict what price will be based on required rate of return and number of years.
def checkIsOnSale(symbol: str, priceData: dict, stocksOnSale: list[str]) -> None:
    stock = yf.Ticker(symbol)
    price = stock.history(period='1d')['Close'][0]
    
    sale_prices = priceData['sale_price']
    if( (sale_prices[0] > 0 and sale_prices[1] > 0 and sale_prices[2] > 0) and (price < sale_prices[0] or price < sale_prices[1] or price < sale_prices[2])):
        print( symbol + " is on sale")
        stocksOnSale.append(symbol)
        df = pd.DataFrame.from_dict(priceData)
        df.to_csv('Output/' + symbol + '.csv', index=False)
    else:
        print( symbol + " is not on sale")

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

class generatorThread (threading.Thread):
   def __init__(self, threadID, name, counter, symbols: list[str]):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      self.symbols = symbols
   def run(self):
        for symbol in self.symbols:
            try:
                checkIsOnSale(symbol, calculator.calculate_sticker_price_data(symbol), stocksOnSale)
            except Exception as e: 
                print("Could not retrieve data for " + symbol, e)
            processedSymbols.append(symbol)

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

    calculator.download_historical_data(stocks[:50])

    if( len(stocks)%MAX_NUMBER_OF_THREADS == 0 ):
        step = int(len(stocks)/MAX_NUMBER_OF_THREADS)
    else:
        step = int(len(stocks)/MAX_NUMBER_OF_THREADS) + 1

    threads = []
    stock_groups = []
    for i in range(0, len(stocks), step):
        stock_groups.append(stocks[i:i+step])
    for i in range(len(stock_groups)):
        threads.append(generatorThread(i + 1, "thread_" + str(i + 1), i+1, symbols = stock_groups[i]))
        threads[int(i)].start()
    for t in threads:
        t.join()
    del(threads)
    
    with open(r'processedSymbols.txt', 'a') as fp:
        for symbol in processedSymbols:
            fp.write("%s\n" % symbol)

    end = time.time()
    
    print("Sticker Price Analysis Complete\nElapsed time: %2d minutes, %2d seconds\n" % ((end - startTime)/60, (end - startTime)%60))
    print(stocksOnSale)