import time
import sys
import Source.ComponentFactory as CF
import Source.Helper.Helper as Helper
import sys
import os


sys.path.extend([
    f'./{name}' for name in os.listdir(".") if os.path.isdir(name)
])

MAX_NUMBER_OF_THREADS: int = 10
helper: Helper.helper = CF.ComponentFactory.getHelperObject()

if __name__ == "__main__":

    processedSymbols: list[str] = []
    stocks = sys.argv[1:]

    startTime = time.time()

    try:
        if (len(stocks) == 0):
            helper.retrieve_stock_list(stocks)
        h_data = helper.download_historical_data(stocks)
    except Exception as e:
        raise Exception('Error: Could not build stock list - ', e)

    if (len(stocks) % MAX_NUMBER_OF_THREADS == 0):
        step = int(len(stocks)/MAX_NUMBER_OF_THREADS)
    else:
        step = int(len(stocks)/MAX_NUMBER_OF_THREADS) + 1

    threads = []
    stock_groups = []
    for i in range(0, len(stocks), step):
        stock_groups.append(stocks[i:i+step])
    for i in range(len(stock_groups)):
        threads.append(CF.ComponentFactory.getPriceCheckWorker(
            i + 1,
            "thread_" + str(i + 1),
            i+1,
            symbols=stock_groups[i],
            h_data=h_data,
            facts=helper.retrieve_bulk_facts(stock_groups[i])
        ))
        threads[int(i)].start()
    for t in threads:
        t.join()
    del (threads)

    end = time.time()

    print("""Sticker Price Analysis Complete\n
            Elapsed time: %2d minutes, %2d seconds\n"""
          % ((end - startTime)/60, (end - startTime) % 60))
