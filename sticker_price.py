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

#Template for later API calls
def retrieve_data(function: str, symbol: str, api_key: str) -> dict:
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={api_key}'
    response = requests.get(url)
    data = response.text
    return json.loads(data)

def retrieve_balance_sheets(symbol: str, api_key: str):
    balance_sheets = retrieve_data('BALANCE_SHEET', symbol, api_key)['quarterlyReports']
    return balance_sheets

def retrieve_current_EPS(symbol: str, api_key: str):
    current_eps = 0
    quarterly_EPS = retrieve_data('EARNINGS', symbol, api_key)['quarterlyEarnings'][0:4]
    for quarter in quarterly_EPS:
        current_eps += round(float(quarter['reportedEPS']), 2)
    return current_eps

def retrieve_annual_PE(symbol: str, api_key: str):
    annual_EPS = retrieve_data('EARNINGS', symbol, api_key)['annualEarnings'][0:5]
    annual_PE = []

    for year in annual_EPS:
        h_data = yf.download(symbol, year['fiscalDateEnding'])['Close']
        price = float(h_data[0])
        eps = float(year['reportedEPS'])
        print(str(year['fiscalDateEnding']) + " --- " + str(price) + " --- " + str(eps))
        annual_PE.append(price/eps)

    return annual_PE

def retrieve_quarterly_BVPS(symbol :str, api_key: str):
    quarterly_BVPS = []
    balance_sheets = retrieve_balance_sheets(symbol, api_key)

    
    for quarter in balance_sheets:
        try:
            quarterly_BVPS.append(round(float(quarter['totalShareholderEquity'])/float(quarter['commonStockSharesOutstanding']), 3))
        except ValueError:
            print(quarter['fiscalDateEnding'] + " Skipped")    
    return quarterly_BVPS

def retrieve_fy_growth_estimate(symbol: str):
    url = "https://www.zacks.com/stock/quote/" + symbol + "/detailed-estimates"
    page = requests.get(url, headers = {'User-Agent' : '008'})
    doc = lh.fromstring(page.content)
    td_elements = doc.xpath('//td')

    for i in range(len(td_elements)):
        if(td_elements[i].text_content() == 'Next 5 Years'):
            return td_elements[i + 1].text_content() 
    
    return -1

if __name__ == '__main__':

    try:
        api_key = os.getenv('ALPHA_API_KEY')
    except:
        os.environ['ALPHA_API_KEY'] = input("Insert alpha vantage API key: ")

    num_years = 10
    percent_return = 15

    #read in symbol to be process
    symbol = 'PAGS'

    #initialize data that will become dataframe
    data = dict()
    annual_BVPS = []

    #retrieve quarterly book value per share data
    quarterly_BVPS = retrieve_quarterly_BVPS(symbol, api_key)

    #annualize this data for dataframe
    i = 0
    while i < len(quarterly_BVPS):
        annual_BVPS.append(statistics.mean(quarterly_BVPS[i: i+4]))
        i += 4

    #add Book Value per share annualized values to dataframe
    data['BVPS'] = annual_BVPS
    
    #calculate trailing twelve month BVPS for 1 year and trailing five month for 5 year
    ttm_BVPS_growth = ((quarterly_BVPS[0]/quarterly_BVPS[3]) ** (1) - 1)*100
    tfy_BVPS_growth = ((quarterly_BVPS[0]/quarterly_BVPS[19]) ** (1/5) - 1)*100

    #Retrieve current EPS and set values for equation
    while(True):
        try:
            current_eps = retrieve_current_EPS(symbol, api_key)
            equity_growth_rate = tfy_BVPS_growth
            forward_PE = sum(data['PE'])/5
            data['PE'] = retrieve_annual_PE(symbol, api_key)
            break
        except KeyError:
            time.sleep(3)
    
    df = pd.DataFrame(data, columns = ['BVPS', 'PE'])
    print(df)

    #If estimates are less than predicted, go with the estimates ( Future Price/Earnings and Future growth rate)
    if forward_PE > equity_growth_rate * 2:
        forward_PE = equity_growth_rate * 2

    analyst_growth_estimate = float(retrieve_fy_growth_estimate(symbol))

    if equity_growth_rate > analyst_growth_estimate:
        equity_growth_rate = analyst_growth_estimate

    print('Current EPS: ', current_eps)
    print('Average equity growth rate: ', equity_growth_rate)
    print('Estimated future PE: ', forward_PE)


    #calculate the sticker price of the stock today relative to what predicted price will be in the future
    time_to_double = np.log(2)/np.log(1 + (equity_growth_rate/100))
    num_of_doubles = num_years/time_to_double
    future_price = forward_PE * current_eps * 2 ** num_of_doubles
    
    return_time_to_double = np.log(2)/np.log(1 + (percent_return/100))
    number_of_equity_doubles = num_years/return_time_to_double
    print(2 ** number_of_equity_doubles)
    sticker_price = future_price/( 2 ** number_of_equity_doubles )

    print("Future Price:  $", sticker_price)
    print("On-Sale Price: $", sticker_price/2)