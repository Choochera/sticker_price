import sys, os
sys.path.extend([f'./{name}' for name in os.listdir(".") if os.path.isdir(name)])
import pandas as pd
import threading
import yfinance as yf
import time
import sys
import Source.ComponentFactory as CF
import Data_Calculator.Data_Calculator as DC
import Helper.Helper as Helper

MAX_NUMBER_OF_THREADS: int = 10
lock: threading.Lock = threading.Lock()
helper: Helper.helper = CF.ComponentFactory.getHelperObject()

# Rule 1 equation application. Uses PE and equity growth to predict what price will be based on required rate of return and number of years.
def checkIsOnSale(symbol: str, priceData: dict, stocksOnSale: list[str]) -> None:
    stock = yf.Ticker(symbol)
    price = stock.history(period='1d')['Close'][0]
    sale_prices = priceData['sale_price']
    if( (sale_prices[0] > 0 and sale_prices[1] > 0 and sale_prices[2] > 0) and (price < sale_prices[0] or price < sale_prices[1] or price < sale_prices[2])):
        print( symbol + " is on sale")
        stocksOnSale.append(symbol)
        helper.add_padding_to_collection(priceData, '')
        df = pd.DataFrame.from_dict(priceData)
        df.to_csv('Output/' + symbol + '.csv', index=False)
    else:
        print( symbol + " is not on sale")

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
                calculator: DC.Data_Calculator = CF.ComponentFactory.getDataCalculatorObject(symbol, self.h_data)
                checkIsOnSale(symbol, calculator.calculate_sticker_price_data(), stocksOnSale)
            except Exception as e: 
                print('Thread ' + str(self.threadID) + " could not retrieve data for " + symbol, e)
            with lock:
                helper.write_processed_symbols(symbol = symbol)

if __name__ == "__main__":

    stocksOnSale: list[str]= []
    processedSymbols: list[str] = []
    stocks = sys.argv[1:]

    startTime = time.time()

    try:
        if( len(stocks) == 0 ):
            helper.retrieve_stock_list(stocks)
        h_data, stocks = helper.download_historical_data(stocks)
    except Exception as e:
        raise Exception('Error: Could not build stock list - ', e)
        
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