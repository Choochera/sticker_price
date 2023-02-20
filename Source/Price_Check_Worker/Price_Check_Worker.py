import Source.Data_Calculator.Data_Calculator as DC
import pandas as pd
import threading
import yfinance as yf
import Source.Helper.IHelper as IHelper
import Source.ComponentFactory as CF
import Source.Price_Check_Worker.IPrice_Check_Worker as IPCW
import Source.constants as const
import os
import asyncio
lock: threading.Lock = threading.Lock()


class priceCheckWorker (threading.Thread, IPCW.IPrice_Check_Worker):

    def __init__(
        self,
        threadID,
        name,
        counter,
        symbols: list[str],
        h_data: dict,
        facts: dict,
        helper: IHelper.IHelper
    ):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.symbols = symbols
        self.h_data = h_data
        self.facts = facts
        self.helper = helper

    def run(self):
        loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.waitForCheckIsOnSale(self.symbols, loop))
        loop.close()

    # Rule 1 equation application. Uses PE and equity growth to predict what
    # price will be based on required rate of return and number of years.
    async def waitForCheckIsOnSale(
            self,
            symbols: str,
            loop: asyncio.AbstractEventLoop) -> None:
        tasks: list[asyncio.Task] = []
        for symbol in symbols:
            tasks.append(loop.create_task(self.checkIsOnSale(
                    symbol
                )))
        await asyncio.wait(tasks)

    async def checkIsOnSale(
            self,
            symbol: str) -> None:
        try:
            if (self.facts is not None):
                symbolFacts = self.facts[symbol]
            else:
                symbolFacts = self.helper.retrieve_facts(symbol)
            calculator = CF.ComponentFactory.getDataCalculatorObject(
                    symbol,
                    self.h_data,
                    symbolFacts
                )
            priceData: dict = calculator.calculate_sticker_price_data()
            stock = yf.Ticker(symbol)
            price = stock.history(period=const.ONE_DAY)[const.CLOSE][0]
            sale_prices = priceData[const.SALE_PRICE]
            if ((sale_prices[0] > 0
                and sale_prices[1] > 0
                and sale_prices[2] > 0) and
                (price < sale_prices[0]
                    and price < sale_prices[1]
                    and price < sale_prices[2])):
                print(const.ON_SALE % symbol)
                self.helper.add_padding_to_collection(priceData, const.EMPTY)
                df = pd.DataFrame.from_dict(priceData)
                if not os.path.exists(const.OUTPUT_PATH):
                    os.makedirs(const.OUTPUT_PATH)
                df.to_csv(const.OUTPUT_CSV_PATH % symbol, index=False)
            else:
                print(const.NOT_ON_SALE % symbol)
        except Exception as e:
            print("Thread %s could not retrieve data"
                  " for %s: " % (self.threadID, symbol), e)
        with lock:
            self.helper.write_processed_symbols(symbol=symbol)
