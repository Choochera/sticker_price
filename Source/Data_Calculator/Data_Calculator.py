
import Source.ComponentFactory as CF
import Source.Exceptions.InsufficientDataException as IDE
import Source.Exceptions.DisqualifyingDataException as DDE
import Source.constants as const
import Source.Data_Calculator.Functions.PE_Calculator as PE_Calculator
import Source.Data_Calculator.Functions.IData_Calculator_Function as IDC
import Source.Data_Calculator.Functions.BVPS_Calculator as BVPS_Calculator
import Source.Data_Calculator.Functions.Price_Calculator as SP_Calculator
import Source.Data_Calculator.Functions.ROIC_Calculator as ROIC_Calculator


class dataCalculator():

    def __init__(self, symbol: str, h_data: dict, facts: dict):
        self.symbol = symbol
        self.h_data = h_data
        self.benchmark_price_sales_ratio = 2.88
        self.facts = facts
        self.function: IDC.IData_Calculator_Function = None
        try:
            self.retriever = CF.ComponentFactory.getDataRetrieverObject(
                self.symbol,
                self.facts
            )
            self.helper = CF.ComponentFactory.getHelperObject()
        except Exception as e:
            raise e

    def calculate_sticker_price_data(self) -> dict:
        priceData = dict()
        priceData[const.TRAILING_YEARS] = []
        priceData[const.STICKER_PRICE] = []
        priceData[const.SALE_PRICE] = []
        priceData[const.RATIO_PRICE] = []
        annual_BVPS = []

        # retrieve quarterly book value per share data
        self.function = BVPS_Calculator.BVPS_Calculator(
            self.symbol,
            self.facts
        )
        self.function.set_variables()
        quarterly_BVPS = self.function.calculate()
        priceData[const.QRTLY_BVPS] = quarterly_BVPS

        # annualize quarterly book values for dataframe consistency
        first_quarter, annual_BVPS = self.function.annualize(quarterly_BVPS)

        # Calculate trailing 10 year annual BVPS growth rate
        try:
            tyy_BVPS_growth = ((
                first_quarter[len(first_quarter) - 1] /
                first_quarter[0]) ** (1/1) - 1) * 100
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

        quarterly_EPS = self.retriever.retrieve_quarterly_EPS()
        self.function = PE_Calculator.PE_Calculator(
            self.symbol,
            self.facts,
            self.h_data
        )
        self.function.set_variables(quarterly_EPS)
        quarterly_PE = PE_Calculator.PE_Calculator.calculate(self.function)
        priceData[const.QRTLY_PE] = quarterly_PE
        annual_PE = self.function.annualize(quarterly_PE)

        # Retrieve current EPS and set values for equation
        priceData[const.QRTLY_EPS] = quarterly_EPS
        annual_EPS = self.__annualize_quarterly_EPS(quarterly_EPS)

        # Retrieve ROIC over passed 10 years
        self.function = ROIC_Calculator.ROIC_Calculator(
            self.symbol,
            self.facts
        )
        self.function.set_variables()
        priceData[const.ROIC] = ROIC_Calculator.ROIC_Calculator.calculate(
            self.function
        )

        periods = [1, 5, 10]
        growth_rates = [tyy_BVPS_growth, tfy_BVPS_growth, tty_BVPS_growth]

        try:
            analyst_growth_estimate = float(
                self.retriever.retrieve_fy_growth_estimate()
            )
        except ValueError:
            analyst_growth_estimate = const.NA

        self.function = SP_Calculator.Price_Calculator()
        for i in range(3):
            self.function.set_variables(
                periods[i],
                growth_rates[i],
                annual_PE,
                annual_EPS,
                analyst_growth_estimate
            )
            self.__append_price_values(
                priceData,
                self.function.calculate()
            )
        priceData[const.RATIO_PRICE].append(
            self.retriever.retrieve_benchmark_ratio_price(
                self.benchmark_price_sales_ratio
                )
            )
        return priceData

    def __append_price_values(self, priceData: dict, additions: dict) -> None:
        priceData[const.TRAILING_YEARS].append(additions[const.TRAILING_YEARS])
        priceData[const.STICKER_PRICE].append(additions[const.STICKER_PRICE])
        priceData[const.SALE_PRICE].append(additions[const.SALE_PRICE])

    def __annualize_quarterly_EPS(
        self,
        quarterly_EPS: list[dict]
    ) -> list[float]:
        if (len(quarterly_EPS) < 40):
            raise IDE.InsufficientDataException(const.EPS)
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
        return annual_EPS
