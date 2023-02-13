
import json
import Source.ComponentFactory as CF
import Source.Exceptions.InsufficientDataException as IDE
import Source.Exceptions.DataRetrievalException as DRE
import Source.Exceptions.DisqualifyingDataException as DDE
from datetime import datetime, timedelta
import statistics
import numpy as np
import Source.Data_Calculator.IData_Calculator as IDC
import Source.constants as const


class dataCalculator(IDC.IData_Calculator):

    def __init__(self, symbol: str, h_data: dict, facts: dict):
        self.symbol = symbol
        self.h_data = h_data
        self.benchmark_price_sales_ratio = 2.88
        self.facts = facts
        try:
            self.retriever = CF.ComponentFactory.getDataRetrieverObject(
                self.symbol,
                self.facts
            )
            self.helper = CF.ComponentFactory.getHelperObject()
        except Exception as e:
            raise e

    def calculate_quarterly_PE(self) -> list[float]:
        # ttm PE = price at earnings announcement / ttm EPS
        quarterly_EPS = self.retriever.retrieve_quarterly_EPS()
        quarterly_PE = []

        for i in range(len(quarterly_EPS)):
            date = datetime.strptime(
                list(quarterly_EPS[i].keys())[0],
                '%Y-%m-%d').date()
            if date.weekday() == 5:
                date = date - timedelta(days=1)
            if date.weekday() == 6:
                date = date - timedelta(days=2)

            date = str(date)
            price = 0
            attempts = 0
            while price == 0 and attempts < 7:
                try:
                    dataForDate = self.h_data.loc[date]
                    price = float(dataForDate[const.ADJ_CLOSE][self.symbol])
                except KeyError:
                    date = datetime.strptime(date, '%Y-%m-%d').date()
                    date = date + timedelta(days=1)
                    date = str(date)
                    attempts += 1

            eps = float(list(quarterly_EPS[i].values())[0])
            try:
                quarterly_PE.append(price/eps)
            except ZeroDivisionError:
                quarterly_PE.append(0)
        return quarterly_PE

    def calculate_quarterly_BVPS(self) -> list[dict]:
        quarterly_BVPS = []
        data = self.retrieve_qrtly_BVPS_variables()
        qrtly_shareholder_equity = data[0]
        qrtly_outstanding_shares = data[1]
        last_share_value = -1
        processedDates = []
        qrtly_outstanding_shares.reverse()
        for equity in qrtly_shareholder_equity:
            if (list(equity.keys())[0] not in str(processedDates)):
                for shares in qrtly_outstanding_shares:
                    equity_key = list(equity.keys())[0]
                    shares_key = list(shares.keys())[0]
                    if (
                        list(equity.keys())[0] not in str(processedDates) and
                        self.helper.days_between(equity_key, shares_key) <= 365
                    ):
                        if shares[shares_key] != 0:
                            last_share_value = shares[shares_key]
                        if shares[shares_key] != 0:
                            val = {
                                equity_key:
                                float(equity[equity_key]) /
                                float(shares[shares_key])
                            }
                        else:
                            val = {
                                equity_key:
                                float(equity[equity_key]) /
                                float(last_share_value)
                            }
                        quarterly_BVPS.append(val)
                        processedDates.append(list(equity.keys())[0])
                processedDates.append(list(equity.keys())[0])
        return quarterly_BVPS

    def calculate_sticker_price(
            self,
            trailing_years: int,
            equity_growth_rate: float,
            annual_PE: list,
            annual_EPS: list,
            analyst_growth_estimate: float) -> dict:

        result = dict()
        forward_PE = statistics.mean(annual_PE)
        current_qrtly_EPS = annual_EPS[0]/4

        if (analyst_growth_estimate == const.NA):
            analyst_growth_estimate = equity_growth_rate.real
            
        # If analyst estimates are lower than the
        # predicted equity growth rate, go with them
        if equity_growth_rate.real > analyst_growth_estimate.real:
            equity_growth_rate = analyst_growth_estimate.real

        # Calculate the sticker price of the stock today
        # relative to what predicted price will be in the future
        num_years = 10
        percent_return = 15

        # # Plug in acquired values into Rule #1 equation

        time_to_double = np.log(2)/np.log(1 + (equity_growth_rate/100))
        num_of_doubles = num_years/time_to_double
        future_price = forward_PE * current_qrtly_EPS * 2 ** num_of_doubles

        return_time_to_double = np.log(2)/np.log(1 + (percent_return/100))
        number_of_equity_doubles = num_years/return_time_to_double
        sticker_price = future_price/(2 ** number_of_equity_doubles)

        result[const.TRAILING_YEARS] = trailing_years
        result[const.STICKER_PRICE] = sticker_price
        result[const.SALE_PRICE] = sticker_price/2

        return result

    def append_price_values(self, priceData: dict, additions: dict) -> None:
        priceData[const.TRAILING_YEARS].append(additions[const.TRAILING_YEARS])
        priceData[const.STICKER_PRICE].append(additions[const.STICKER_PRICE])
        priceData[const.SALE_PRICE].append(additions[const.SALE_PRICE])

    def calculate_sticker_price_data(self) -> dict:
        priceData = dict()
        priceData[const.TRAILING_YEARS] = []
        priceData[const.STICKER_PRICE] = []
        priceData[const.SALE_PRICE] = []
        priceData[const.RATIO_PRICE] = []
        annual_BVPS = []

        # retrieve quarterly book value per share data
        quarterly_BVPS = self.calculate_quarterly_BVPS()
        priceData[const.QRTLY_BVPS] = quarterly_BVPS

        # annualize quarterly book values for dataframe consistency
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
            tyy_BVPS_growth = ((
                first_quarter[0] /
                first_quarter[len(first_quarter) - 1]) ** (1/4) - 1) * 100
            tfy_BVPS_growth = ((
                annual_BVPS[0] / annual_BVPS[4]) ** (1/5) - 1) * 100
            tty_BVPS_growth = ((
                annual_BVPS[0] /
                annual_BVPS[len(annual_BVPS) - 1]
            ) ** (1/len(annual_BVPS)) - 1) * 100
        except IndexError:
            raise IDE.InsufficientDataException(const.H_DATA)

        # Calculate annual PE
        annual_PE = []
        quarterly_PE = self.calculate_quarterly_PE()
        priceData[const.QRTLY_PE] = quarterly_PE

        if (len(quarterly_PE) < 4):
            raise IDE.InsufficientDataException(const.QRTLY_PE)

        i = len(quarterly_PE) - 4
        while i > 0 and i > len(quarterly_PE) - 44:
            quarters = quarterly_PE[i: i+4]
            annual_PE.append(float(sum(quarters)/len(quarters)))
            i -= 4

        # Retrieve current EPS and set values for equation
        quarterly_EPS = self.retriever.retrieve_quarterly_EPS()
        priceData[const.QRTLY_EPS] = quarterly_EPS
        annual_EPS = []
        i = len(quarterly_EPS) - 4
        while i > 0 and i > len(quarterly_EPS) - 44:
            quarters = quarterly_EPS[i: i+4]
            s = 0
            for quarter in quarters:
                s += list(quarter.values())[0]
            if (s < 0):
                raise DDE.DisqualifyingDataException(self.symbol, const.EPS)
            annual_EPS.append(float(s))
            i -= 4

        periods = [1, 5, 10]
        growth_rates = [tyy_BVPS_growth, tfy_BVPS_growth, tty_BVPS_growth]

        try:
            analyst_growth_estimate = float(
                self.retriever.retrieve_fy_growth_estimate())
        except ValueError:
            analyst_growth_estimate = const.NA
            
        for i in range(3):
            self.append_price_values(
                priceData,
                self.calculate_sticker_price(
                    periods[i],
                    growth_rates[i],
                    annual_PE,
                    annual_EPS,
                    analyst_growth_estimate 
                    )
                )
        priceData[const.RATIO_PRICE].append(
            self.retriever.retrieve_benchmark_ratio_price(
                self.benchmark_price_sales_ratio
                )
            )
        return priceData

    def retrieve_qrtly_BVPS_variables(self) -> tuple[list[dict], list[dict]]:
        try:
            a = self.retriever.retrieve_quarterly_shareholder_equity()
        except DRE.DataRetrievalException:
            self.helper.write_error_file(self.symbol, const.EQUITY, const.DRE, self.facts)
        try:
            b = self.retriever.retrieve_quarterly_outstanding_shares()
        except DRE.DataRetrievalException:
            self.helper.write_error_file(self.symbol, const.OUTSTANDING_SHARES, const.DRE, self.facts)
        return a, b
