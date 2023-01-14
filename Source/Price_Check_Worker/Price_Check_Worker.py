import Source.Data_Calculator.Data_Calculator as DC
import pandas as pd
import threading
import yfinance as yf
import Source.Helper.Helper as Helper
import Source.ComponentFactory as CF
import Source.Price_Check_Worker.IPrice_Check_Worker as IPCW

lock: threading.Lock = threading.Lock()

class priceCheckWorker (threading.Thread, IPCW.IPrice_Check_Worker):

    def __init__(self, threadID, name, counter, symbols: list[str], h_data: dict, facts: dict):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      self.symbols = symbols
      self.h_data = h_data
      self.facts = facts
      self.helper = CF.ComponentFactory.getHelperObject()

    def run(self):
        for symbol in self.symbols:
            try:
                calculator: DC.Data_Calculator = CF.ComponentFactory.getDataCalculatorObject(symbol, self.h_data, self.facts)
                self.checkIsOnSale(symbol, calculator.calculate_sticker_price_data())
            except Exception as e: 
                print('Thread ' + str(self.threadID) + " could not retrieve data for " + symbol, e)
            with lock:
                self.helper.write_processed_symbols(symbol = symbol)
    
    # Rule 1 equation application. Uses PE and equity growth to predict what price will be based on required rate of return and number of years.
    def checkIsOnSale(self, symbol: str, priceData: dict) -> None:
        stock = yf.Ticker(symbol)
        price = stock.history(period='1d')['Close'][0]
        sale_prices = priceData['sale_price']
        if( (sale_prices[0] > 0 and sale_prices[1] > 0 and sale_prices[2] > 0) and (price < sale_prices[0] or price < sale_prices[1] or price < sale_prices[2])):
            print( symbol + " is on sale")
            self.helper.add_padding_to_collection(priceData, '')
            df = pd.DataFrame.from_dict(priceData)
            df.to_csv('Output/' + symbol + '.csv', index=False)
        else:
            print( symbol + " is not on sale")
