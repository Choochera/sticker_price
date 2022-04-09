import json
import requests
import pandas as pd
import numpy as np
import time
import yfinance as yf
import sys
import statistics
import requests
import lxml.html as lh
import os
from currency_converter import CurrencyConverter

# Rule 1 equation application. Uses PE and equity growth to predict what price will be based on required rate of return and number of years.

def retrieve_data(function: str, symbol: str, api_key: str) -> dict:
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={api_key}'
    try:
        response = requests.get(url)
        data = response.text
    except requests.exceptions.HTTPError as hError:
        raise Exception(str("Http Error:", hError))
    except requests.exceptions.ConnectionError as cError:
        raise Exception(str("Error Connecting:", cError))
    except requests.exceptions.Timeout as tError:
        raise Exception(str("Timeout Error:", tError))
    except requests.exceptions.RequestException as rError:
        raise Exception(str("Other Error:", rError))

    #Make limited attempts to retrieve data from API
    attempts = 0
    while(attempts <= 3):
        try: 
            json.loads(data)['Note']
            attempts += 1
            time.sleep(3) #log message 
            print('Attempt ' + str(attempts) + ' failed to retrieve data from API. Trying again...')
        except KeyError:
            return json.loads(data)

    #In even of exceeded API use, HTTP error is thrown
    raise Exception('Total API Calls Exceeded - please wait and try again')

def retrieve_balance_sheets(symbol: str, api_key: str):
    try:
        result = retrieve_data('BALANCE_SHEET', symbol, api_key)['quarterlyReports']
    except KeyError:
        raise KeyError(str(symbol) + " is not a valid symbol!")
    return result

def retrieve_current_EPS(symbol: str, api_key: str):
    quarterly_EPS = retrieve_data('EARNINGS', symbol, api_key)

    #Isolate the last four quarters (or less if that is unavailable)
    if(len(quarterly_EPS) > 4):
        quarterly_EPS = quarterly_EPS['quarterlyEarnings'][0:4]
    else: 
        quarterly_EPS = quarterly_EPS['quarterlyEarnings'][0 : len(quarterly_EPS)]

    #Accumulate EPS for the passed four quarterly earnings
    current_eps = 0
    for quarter in quarterly_EPS:
        current_eps += round(float(quarter['reportedEPS']), 3)

    return current_eps

def retrieve_annual_PE(symbol: str, api_key: str, num_years: int):

    # ttm PE = price at earnings announcement / ttm EPS
    quarterly_EPS = retrieve_data('EARNINGS', symbol, api_key)['quarterlyEarnings']
    annual_PE = []

    # Calculating ttm EPS for each respective annual PE
    # Start at earliest report date
    i = 0
    while i + 4 < len(quarterly_EPS) and i < num_years * 4:
        h_data = yf.download(symbol, quarterly_EPS[i]['reportedDate'])['Close']
        price = float(h_data[0])

        eps = 0
        for quarter in quarterly_EPS[i : i + 4]:
            eps += float(quarter['reportedEPS'])

        print(str(quarterly_EPS[i]['reportedDate']) + " --- " + str(price) + " --- " + str(eps))
        annual_PE.append(price/eps)
        i += 4 #Move on to next set of 4 quarters (or 1 year)

    if( len(annual_PE) != num_years ):
            eps = float(quarterly_EPS[len(quarterly_EPS) - 1]['reportedEPS'])
            h_data = yf.download(symbol, quarterly_EPS[len(quarterly_EPS) - 1]['reportedDate'])['Close']
            price = float(h_data[0])
            annual_PE.append(price/eps)

    return annual_PE

def retrieve_quarterly_BVPS(symbol :str, api_key: str):
    quarterly_BVPS = []
    balance_sheets = retrieve_balance_sheets(symbol, api_key)

    c = CurrencyConverter()
    currency = 'USD'
    
    if(balance_sheets[0]['reportedCurrency'] != 'USD'):
        currency = balance_sheets[0]['reportedCurrency']

    for quarter in balance_sheets:
        try:
            if( float(quarter['totalShareholderEquity']) < 0): raise Exception ("Negative BVPS within the passed 5 years - not a rule 1 company")
            quarterly_BVPS.append(round(float(c.convert(quarter['totalShareholderEquity'], currency, 'USD'))/float(quarter['commonStockSharesOutstanding']), 3))
        except ValueError:
            print(quarter['fiscalDateEnding'] + " Skipped")   

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

if __name__ == '__main__':

    #Access OS environmental variable alpha key, or save a new one
    try:
        api_key = os.getenv('ALPHA_API_KEY')
    except:
        os.environ['ALPHA_API_KEY'] = input("Insert alpha vantage API key: ")

    #read in symbol to be process
    symbol = sys.argv[1]

    #initialize data that will become dataframe
    data = dict()
    annual_BVPS = []

    try:    
        #retrieve quarterly book value per share data
        quarterly_BVPS = retrieve_quarterly_BVPS(symbol, api_key)

        #annualize quarterly book values for dataframe consistency
        i = 0
        while i < len(quarterly_BVPS) and i < 20:
            annual_BVPS.append(statistics.mean(quarterly_BVPS[i: i+4]))
            i += 4

        #Add Book Value per share annualized values to dataframe
        data['BVPS'] = annual_BVPS
        
        # Calculate trailing 5 year annual BVPS growth rate
        try:
            tfy_BVPS_growth = ( ( annual_BVPS[0]/annual_BVPS[len(annual_BVPS) - 1] ) ** ( 1/len(annual_BVPS) ) - 1 ) * 100
            if( tfy_BVPS_growth < 0 ): raise Exception("Equity growth rate is negative - not a rule 1 company")
        except IndexError:
            raise Exception("Not enough historical data available for symbol: " + symbol)

        # Retrieve current EPS and set values for equation
        data['PE'] = retrieve_annual_PE(symbol, api_key, len(data['BVPS']))
        current_eps = retrieve_current_EPS(symbol, api_key)
        equity_growth_rate = tfy_BVPS_growth
        forward_PE = sum(data['PE'])/5

        df = pd.DataFrame(data, columns = ['BVPS', 'PE'])
        print(df)

        # If estimates are less than predicted, go with the estimates ( Future Price/Earnings and Future growth rate )
        if forward_PE > equity_growth_rate * 2:
            forward_PE = equity_growth_rate * 2

        try:
            analyst_growth_estimate = float(retrieve_fy_growth_estimate(symbol))
        except ValueError:
            print("No analyst growth rate available")
            analyst_growth_estimate = equity_growth_rate.real

        # If analyst estimates are lower than predicted equity growth rate, go with them
        if equity_growth_rate > analyst_growth_estimate.real:
            equity_growth_rate = analyst_growth_estimate.real

        print('Current EPS: ', current_eps)
        print('Average equity growth rate: ', equity_growth_rate)
        print('Estimated future PE: ', forward_PE)

        # Calculate the sticker price of the stock today relative to what predicted price will be in the future
        num_years = 10
        percent_return = 15

        # Plug in acquired values into Rule #1 equation
        time_to_double = np.log(2)/np.log(1 + (equity_growth_rate/100))
        num_of_doubles = num_years/time_to_double
        future_price = forward_PE * current_eps * 2 ** num_of_doubles
        
        return_time_to_double = np.log(2)/np.log(1 + (percent_return/100))
        number_of_equity_doubles = num_years/return_time_to_double
        print(2 ** number_of_equity_doubles)
        sticker_price = future_price/( 2 ** number_of_equity_doubles )

        print("Sticker Price:  $", sticker_price)
        print("On-Sale Price: $", sticker_price/2)
    
    except Exception as e:
        print(str(e))