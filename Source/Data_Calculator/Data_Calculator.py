
import Source.ComponentFactory
from datetime import datetime, timedelta
import statistics
import numpy as np
import Data_Calculator.IData_Calculator

class dataCalculator(Data_Calculator.IData_Calculator.IData_Calculator):

    def __init__(self, symbol: str, h_data: dict):
        self.symbol = symbol
        self.retriever = Source.ComponentFactory.ComponentFactory.getDataRetrieverObject(self.symbol)
        self.h_data = h_data

    def calculate_quarterly_PE(self) -> list[float]:
        # ttm PE = price at earnings announcement / ttm EPS
        quarterly_EPS = self.retriever.retrieve_quarterly_EPS()
        quarterly_PE=[]

        for i in range(len(quarterly_EPS)):
            date = datetime.strptime(list(quarterly_EPS[i].keys())[0], '%Y-%m-%d').date()
            if date.weekday() == 5:
                date = date - timedelta(days = 1)
            if date.weekday() == 6:
                date = date - timedelta(days = 2)
            
            date = str(date)
            price = 0
            while price == 0:
                try:
                    price = float(self.h_data.loc[date]['Adj Close'][self.symbol])
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

    def calculate_quarterly_BVPS(self) -> list[dict]:
        quarterly_BVPS = []
        try: 
            qrtly_shareholder_equity = self.retriever.retrieve_quarterly_shareholder_equity()
            qrtly_outstanding_shares = self.retriever.retrieve_quarterly_outstanding_shares()
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

    def calculate_sticker_price(self, trailing_years: int, equity_growth_rate: float, annual_PE: list, annual_EPS: list) -> dict:
        result = dict()
        forward_PE = statistics.mean(annual_PE)
        current_qrtly_EPS = annual_EPS[0]/4


        # # If estimates are less than predicted, go with the estimates ( Future Price/Earnings and Future growth rate )
        # if forward_PE > equity_growth_rate * 2:
        #     forward_PE = equity_growth_rate * 2

        try:
            analyst_growth_estimate = float(self.retriever.retrieve_fy_growth_estimate())
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
        result['ratio_price'] = self.retriever.retrieve_benchmark_ratio_price(benchmark_price_sales_ratio)

        return result

    def append_price_values(self, priceData: dict, additions: dict) -> None:
        priceData['trailing_years'].append(additions['trailing_years'])
        priceData['sticker_price'].append(additions['sticker_price'])
        priceData['sale_price'].append(additions['sale_price'])
        priceData['ratio_price'].append(additions['ratio_price'])

    def calculate_sticker_price_data(self) -> dict:
        priceData = dict()
        priceData['trailing_years']=[]
        priceData['sticker_price']=[]
        priceData['sale_price']=[]
        priceData['ratio_price']=[]
        annual_BVPS = []

        #retrieve quarterly book value per share data
        quarterly_BVPS = self.calculate_quarterly_BVPS()
        priceData['quarterly_bvps'] = quarterly_BVPS

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
            raise Exception("Not enough historical data available for symbol: " + self.symbol)

        # Calculate annual PE
        annual_PE = []
        quarterly_PE = self.calculate_quarterly_PE()
        priceData['quarterly_pe'] = quarterly_PE

        if ( len(quarterly_PE) < 4 ):
            raise Exception("Not enough quarterly data")

        i = len(quarterly_PE) - 4
        while i > 0 and i > len(quarterly_PE) - 44:
            quarters = quarterly_PE[i: i+4]
            annual_PE.append(float(sum(quarters)/len(quarters)))
            i -= 4

        # Retrieve current EPS and set values for equation
        quarterly_EPS = self.retriever.retrieve_quarterly_EPS()
        priceData['quarterly_eps'] = quarterly_EPS
        annual_EPS = []
        i = len(quarterly_EPS) - 4
        while i > 0 and i > len(quarterly_EPS) - 44:
            quarters = quarterly_EPS[i: i+4]
            s = 0
            for quarter in quarters:
                s += list(quarter.values())[0]
            if(s < 0):
                raise Exception(self.symbol + " has negative annual EPS")
            annual_EPS.append(float(s))
            i -= 4
        self.append_price_values(priceData, self.calculate_sticker_price(1, tyy_BVPS_growth, annual_PE, annual_EPS))
        self.append_price_values(priceData, self.calculate_sticker_price(5, tfy_BVPS_growth, annual_PE, annual_EPS))
        self.append_price_values(priceData, self.calculate_sticker_price(10, tty_BVPS_growth, annual_PE, annual_EPS))
        
        return priceData