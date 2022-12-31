import json
import requests
import pandas as pd
import numpy as np
import threading
import yfinance as yf
import time
import statistics
import requests
import lxml.html as lh
import sys
from datetime import datetime, timedelta

MAX_NUMBER_OF_THREADS=16
h_data = dict()

# Rule 1 equation application. Uses PE and equity growth to predict what price will be based on required rate of return and number of years.
def send_SEC_api_request(symbol: str, element: str):
    headers = {'User-Agent': "your@email.com"}
    tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
    tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
    tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
    cik = tickers_cik[tickers_cik["ticker"] == symbol]['cik_str']
    cik = cik.reset_index(drop = True)
    url = "https://data.sec.gov/api/xbrl/companyconcept/CIK" + cik[0] + "/us-gaap/" + element + ".json"
    response = requests.get(url, headers=headers)
    return response

def retrieve_quarterly_shareholder_equity(symbol: str):
    response = send_SEC_api_request(symbol, "StockholdersEquity")
    try:
        data = response.json()
    except json.decoder.JSONDecodeError:
        raise Exception('Stockholders equity data not available')

    qrtly_shareholder_equity = []
    for i in range(len(data['units']['USD'])):
        val = {
            data['units']['USD'][i]['end']: float(data['units']['USD'][i]['val'])
        }
        qrtly_shareholder_equity.append(val)
    return qrtly_shareholder_equity

def retrieve_quarterly_outstanding_shares(symbol: str):
    try:
        response = send_SEC_api_request(symbol, "CommonStockSharesIssued")
        data = response.json()
    except json.decoder.JSONDecodeError:
        response = send_SEC_api_request(symbol, "CommonStockSharesOutstanding")
        data = response.json()

    qrtly_outstanding_shares = []
    for i in range(len(data['units']['shares'])):
        val = {
            data['units']['shares'][i]['end']: float(data['units']['shares'][i]['val']),
        }
        qrtly_outstanding_shares.append(val)
    return qrtly_outstanding_shares

def retrieve_quarterly_EPS(symbol: str):
    quarterly_EPS = send_SEC_api_request(symbol, 'EarningsPerShareBasic')
    data = quarterly_EPS.json()
    quarterly_EPS = []
    for period in data['units']['USD/shares']:
        try:
            if 'Q' in period['frame']:
                val = {
                    period['end']: float(period['val']),
                }
                quarterly_EPS.append(val)
        except:
            #Skip values without frame 
            None
    
    return quarterly_EPS

def retrieve_historical_data(symbols: list[str]):
    global h_data
    h_data = yf.download(symbols, period="10y")

def retrieve_quarterly_PE(symbol: str):
    global h_data
    # ttm PE = price at earnings announcement / ttm EPS
    quarterly_EPS = retrieve_quarterly_EPS(symbol)
    quarterly_PE=[]

    # Calculating ttm EPS for each respective annual PE
    # Start at earliest report date

    for i in range(len(quarterly_EPS)):
        date = datetime.strptime(list(quarterly_EPS[i].keys())[0], '%Y-%m-%d').date()
        if date.weekday() == 5:
            date = date - timedelta(days = 1)
        if date.weekday() == 6:
            date = date + timedelta(days = 2)
        
        date = str(date)
        price = 0
        while price == 0:
            try:
                price = float(h_data.loc[date]['Adj Close'][symbol])
            except KeyError:
                date = datetime.strptime(date, '%Y-%m-%d').date()
                date = date + timedelta(days= 1)
                date = str(date)

        eps = float(list(quarterly_EPS[i].values())[0])
        try:
            quarterly_PE.append(price/eps)
        except ZeroDivisionError:
            quarterly_PE.append(0)

    return quarterly_PE

def retrieve_quarterly_BVPS(symbol :str):
    quarterly_BVPS = []
    try: 
        qrtly_shareholder_equity = retrieve_quarterly_shareholder_equity(symbol)
        qrtly_outstanding_shares = retrieve_quarterly_outstanding_shares(symbol)
    except Exception as e:
        raise Exception("Cannot retrieve quarterly BVPS - ", e)

    last_share_value = -1
    for equity in qrtly_shareholder_equity:
        for shares in qrtly_outstanding_shares:
            equity_key = list(equity.keys())[0]
            shares_key = list(shares.keys())[0]
            if equity_key == shares_key:
                if(shares[shares_key] != 0):
                    last_share_value = shares[shares_key]
                if(shares[shares_key] != 0):
                    val = {
                        equity_key: float(equity[equity_key])/float(shares[shares_key])
                    }
                else:
                    val = {
                        equity_key: float(equity[equity_key])/float(last_share_value)
                    }
                quarterly_BVPS.append(val)

    return quarterly_BVPS

def retrieve_fy_growth_estimate(symbol: str):
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

def retrieve_benchmark_ratio_price(symbol: str, benchmark: float):
    ttm_revenue: float = 0
    qrtly_revenue = []
    # Calculate ttm revenue total by adding reported revenues from last 4 quarters
    try:
        revenue = send_SEC_api_request(symbol, 'GrossProfit').json()
    except json.decoder.JSONDecodeError:
        revenue = send_SEC_api_request(symbol, 'Revenues').json()

    for period in revenue['units']['USD']:
        try:
            if 'Q' in period['frame']:
                qrtly_revenue.append(float(period['val']))
        except:
            #Skip values without frame 
            None
    shares_outstanding = send_SEC_api_request(symbol, 'CommonStockSharesIssued').json()
    shares_outstanding = shares_outstanding['units']['shares'][len(shares_outstanding['units']['shares']) - 1]['val']
    ttm_revenue = sum(qrtly_revenue[-4:])

    # Equation for price based on provided market benchmark = (revenue / shares outstanding) * benchmark price-sales ratio
    return round(ttm_revenue / float(shares_outstanding), 3) * benchmark

def calculate_sticker_price(symbol, trailing_years, equity_growth_rate, annual_PE, annual_EPS):
    result = dict()
    forward_PE = statistics.mean(annual_PE)
    current_qrtly_EPS = annual_EPS[0]/4


    # # If estimates are less than predicted, go with the estimates ( Future Price/Earnings and Future growth rate )
    # if forward_PE > equity_growth_rate * 2:
    #     forward_PE = equity_growth_rate * 2

    try:
        analyst_growth_estimate = float(retrieve_fy_growth_estimate(symbol))
    except ValueError:
        analyst_growth_estimate = equity_growth_rate.real

    # # If analyst estimates are lower than predicted equity growth rate, go with them
    if equity_growth_rate.real > analyst_growth_estimate.real:
        equity_growth_rate = analyst_growth_estimate.real

    # # Calculate the sticker price of the stock today relative to what predicted price will be in the future
    num_years = 5
    percent_return = 15
    benchmark_price_sales_ratio = 2.88

    # # Plug in acquired values into Rule #1 equation

    time_to_double = np.log(2)/np.log(1 + (equity_growth_rate/100))
    num_of_doubles = num_years/time_to_double
    future_price = forward_PE * current_qrtly_EPS * 2 ** num_of_doubles
    
    return_time_to_double = np.log(2)/np.log(1 + (percent_return/100))
    number_of_equity_doubles = num_years/return_time_to_double
    sticker_price = future_price/( 2 ** number_of_equity_doubles )

    result['trailing_years'] = trailing_years
    result['sticker_price'] = sticker_price
    result['sale_price'] = sticker_price/2

    try:
        result['ratio_price'] = retrieve_benchmark_ratio_price(symbol, benchmark_price_sales_ratio)
    except json.decoder.JSONDecodeError:
        result['ratio_price'] = 0

    return result
        
def append_price_values(priceData: dict, additions: dict):
    priceData['trailing_years'].append(additions['trailing_years'])
    priceData['sticker_price'].append(additions['sticker_price'])
    priceData['sale_price'].append(additions['sale_price'])
    priceData['ratio_price'].append(additions['ratio_price'])

def retrieve_sticker_price_data(symbol: str):

    priceData = dict()
    priceData['trailing_years']=[]
    priceData['sticker_price']=[]
    priceData['sale_price']=[]
    priceData['ratio_price']=[]

    annual_BVPS = []

    #retrieve quarterly book value per share data
    quarterly_BVPS = retrieve_quarterly_BVPS(symbol)

    #annualize quarterly book values for dataframe consistency
    first_quarter = []
    i = len(quarterly_BVPS) - 4
    while i > 0 and i > len(quarterly_BVPS) - 44:
        quarters = quarterly_BVPS[i: i+4]
        s = 0
        for quarter in quarters:
            s += list(quarter.values())[0]
            if len(annual_BVPS) == 0:
                first_quarter.append(list(quarter.values())[0])
        annual_BVPS.append(float(s/len(quarters)))
        i -= 4
    
    # Calculate trailing 10 year annual BVPS growth rate
    try:
        tyy_BVPS_growth = ( ( first_quarter[0]/first_quarter[len(first_quarter) - 1] ) ** ( 1/4 ) - 1 ) * 100
        tfy_BVPS_growth = ( ( annual_BVPS[0]/annual_BVPS[4] ) ** ( 1/5 ) - 1 ) * 100
        tty_BVPS_growth =  ( ( annual_BVPS[0]/annual_BVPS[len(annual_BVPS) - 1] ) ** ( 1/len(annual_BVPS) ) - 1 ) * 100
    except IndexError:
        raise Exception("Not enough historical data available for symbol: " + symbol)

    # Calculate annual PE
    annual_PE = []
    quarterly_PE = retrieve_quarterly_PE(symbol)
    i = len(quarterly_PE) - 4
    while i > 0 and i > len(quarterly_PE) - 44:
        quarters = quarterly_PE[i: i+4]
        annual_PE.append(float(sum(quarters)/len(quarters)))
        i -= 4

    # Retrieve current EPS and set values for equation
    quarterly_EPS = retrieve_quarterly_EPS(symbol)
    annual_EPS = []
    i = len(quarterly_EPS) - 4
    while i > 0 and i > len(quarterly_EPS) - 44:
        quarters = quarterly_EPS[i: i+4]
        s = 0
        for quarter in quarters:
            s += list(quarter.values())[0]
        if(s < 0):
            raise Exception(symbol + " has negative annual EPS")
        annual_EPS.append(float(s))
        i -= 4
    append_price_values(priceData, calculate_sticker_price(symbol, 1, tyy_BVPS_growth, annual_PE, annual_EPS))
    append_price_values(priceData, calculate_sticker_price(symbol, 5, tfy_BVPS_growth, annual_PE, annual_EPS))
    append_price_values(priceData, calculate_sticker_price(symbol, 10, tty_BVPS_growth, annual_PE, annual_EPS))
    
    return priceData

def checkIsOnSale(symbol: str, priceData: dict, stocksOnSale: list[str]):
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

class generatorThread (threading.Thread):
   def __init__(self, threadID, name, counter, symbols):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      self.symbols = symbols
   def run(self):
        for symbol in self.symbols:
            try:
                checkIsOnSale(symbol, retrieve_sticker_price_data(symbol), stocksOnSale)
            except Exception as e: 
                print("Could not retrieve data for " + symbol, e)

if __name__ == "__main__":

    stocksOnSale = []

    #read in symbol to be process
    stocks = sys.argv[1:]
    if(len(stocks) == 0):
        with open('stockList.txt') as f:
            lines = f.readlines()
            for line in lines:
                stock = line.split('\n')[0]
                if(len(stock) > 0):
                    stocks.append(stock)
    
    startTime = time.time()

    retrieve_historical_data(stocks)
    threads = []
    beginning = 0
    end = len(stocks)
    step = 16
    for i in range(beginning, end, step):
        threads.append(generatorThread(i + 1, "thread_" + str(i + 1), i+1, stocks[i:i+step]))
        threads[int(i/16)].start()
    for t in threads:
        t.join()
    del(threads)

    end = time.time()
    
    print("Sticker Price Analysis Complete\nElapsed time: %2d minutes, %2d seconds\n" % ((end - startTime)/60, (end - startTime)%60))
    print(stocksOnSale)