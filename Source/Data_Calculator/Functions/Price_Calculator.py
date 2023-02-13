
import Source.ComponentFactory as CF
import Source.Exceptions.DataRetrievalException as DRE
import Source.Data_Calculator.Functions.IData_Calculator_Function as IDC
import Source.constants as const
import numpy as np
import statistics


class Price_Calculator(IDC.IData_Calculator_Function):

    def __init__(
        self
    ):
        self.trailing_years: int
        self.equity_growth_rate: float
        self.annual_PE: list
        self.annual_EPS: list
        self.analyst_growth_estimate: float

    def calculate(self) -> dict:
        result = dict()
        forward_PE = statistics.mean(self.annual_PE)
        current_qrtly_EPS = self.annual_EPS[0]/4

        if (self.analyst_growth_estimate == const.NA):
            self.analyst_growth_estimate = self.equity_growth_rate.real

        # If analyst estimates are lower than the
        # predicted equity growth rate, go with them
        if self.equity_growth_rate.real > self.analyst_growth_estimate.real:
            self.equity_growth_rate = self.analyst_growth_estimate.real

        # Calculate the sticker price of the stock today
        # relative to what predicted price will be in the future
        num_years = 10
        percent_return = 15

        # # Plug in acquired values into Rule #1 equation

        time_to_double = np.log(2)/np.log(1 + (self.equity_growth_rate/100))
        num_of_doubles = num_years/time_to_double
        future_price = forward_PE * current_qrtly_EPS * 2 ** num_of_doubles

        return_time_to_double = np.log(2)/np.log(1 + (percent_return/100))
        number_of_equity_doubles = num_years/return_time_to_double
        sticker_price = future_price/(2 ** number_of_equity_doubles)

        result[const.TRAILING_YEARS] = self.trailing_years
        result[const.STICKER_PRICE] = sticker_price
        result[const.SALE_PRICE] = sticker_price/2

        return result

    def set_variables(
        self,
        trailing_years: int,
        equity_growth_rate: float,
        annual_PE: list,
        annual_EPS: list,
        analyst_growth_estimate: float
    ) -> None:
        self.trailing_years = trailing_years
        self.equity_growth_rate = equity_growth_rate
        self.annual_PE = annual_PE
        self.annual_EPS = annual_EPS
        self.analyst_growth_estimate = analyst_growth_estimate
