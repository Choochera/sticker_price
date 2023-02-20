
import Source.ComponentFactory as CF
import Source.Exceptions.DataRetrievalException as DRE
import Source.Data_Calculator.Functions.IData_Calculator_Function as IDC
import Source.constants as const


class ROIC_Calculator(IDC.IData_Calculator_Function):

    def __init__(
        self,
        symbol: str,
        facts: dict
    ):
        super().__init__(symbol, facts)
        self.quarterly_net_income = None,
        self.quarterly_shareholder_equity = None,
        self.quarterly_long_term_debt = None

        try:
            self.retriever = CF.ComponentFactory.getDataRetrieverObject(
                self.symbol,
                self.facts
            )
            self.helper = CF.ComponentFactory.getHelperObject()
        except Exception as e:
            raise e

    def calculate(self) -> list[float]:
        annual_income = self.__calculate_annual_income()
        quarterly_IC = self.__calculate_quarterly_IC()
        annual_ROIC = []
        processedDates = []
        for income in annual_income:
            date = list(income.keys())[0]
            if (date not in str(processedDates)):
                for investedCapital in reversed(quarterly_IC):
                    income_key = list(income.keys())[0]
                    investedCapital_key = list(investedCapital.keys())[0]
                    if (
                        list(income.keys())[0] not in str(processedDates) and
                        self.helper.days_between(income_key, investedCapital_key) <= 365
                    ):
                        val = {
                            income_key:
                            (float(income[income_key]) /
                            float(investedCapital[investedCapital_key])) * 100
                        }
                        annual_ROIC.insert(0, val)
                        processedDates.append(list(income.keys())[0])
        return annual_ROIC

    def set_variables(self) -> None:
        try:
            a = self.retriever.retrieve_quarterly_net_income()
        except DRE.DataRetrievalException as e:
            self.helper.write_error_file(
                self.symbol,
                const.NET_INCOME_LOSS,
                const.DRE,
                self.facts
            )
            raise e
        try:
            b = self.retriever.retrieve_quarterly_shareholder_equity()
        except DRE.DataRetrievalException as e:
            self.helper.write_error_file(
                self.symbol,
                const.EQUITY,
                const.DRE,
                self.facts
            )
            raise e
        try:
            c = self.retriever.retrieve_quarterly_long_term_debt()
        except DRE.DataRetrievalException as e:
            self.helper.write_error_file(
                self.symbol,
                const.LONG_TERM_DEBT,
                const.DRE,
                self.facts
            )
            raise e

        self.quarterly_net_income = a
        self.quarterly_shareholder_equity = b
        self.quarterly_long_term_debt = c

    def __calculate_quarterly_IC(self) -> list[dict]:
        quarterly_IC = []
        processedDates = []
        for equity in self.quarterly_shareholder_equity:
            date = list(equity.keys())[0]
            if (date not in str(processedDates)):
                for debt in self.quarterly_long_term_debt:
                    equity_key = list(equity.keys())[0]
                    debt_key = list(debt.keys())[0]
                    if (
                        list(equity.keys())[0] not in str(processedDates) and
                        self.helper.days_between(equity_key, debt_key) <= 90
                    ):
                        val = {
                            equity_key:
                            float(equity[equity_key]) +
                            float(debt[debt_key])
                        }
                        quarterly_IC.append(val)
                        processedDates.append(list(equity.keys())[0])
                processedDates.append(list(equity.keys())[0])
        return quarterly_IC

    def __calculate_annual_income(self) -> list[dict]:
        annual_income: list[float]  = []
        sum: float = 0
        numQuarters: int = 0
        for quarter in reversed(self.quarterly_net_income):
            date = list(quarter.keys())[0]
            if (numQuarters == 0):
                endDate = date
            sum += quarter[date]
            numQuarters += 1 
            if (numQuarters == 4):
                val = {
                    endDate: sum
                }
                annual_income.append(val)
                sum = 0
                numQuarters = 0
        return annual_income
