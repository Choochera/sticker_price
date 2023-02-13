
import Source.ComponentFactory as CF
from datetime import datetime, timedelta
import Source.Data_Calculator.Functions.IData_Calculator_Function as IDC
import Source.constants as const


class PE_Calculator(IDC.IData_Calculator_Function):

    def __init__(
        self,
        symbol: str,
        facts: dict,
        h_data: dict
    ):
        super().__init__(symbol, facts)
        self.h_data = h_data
        self.quarterly_EPS = None

        try:
            self.retriever = CF.ComponentFactory.getDataRetrieverObject(
                self.symbol,
                self.facts
            )
            self.helper = CF.ComponentFactory.getHelperObject()
        except Exception as e:
            raise e

    def calculate(self) -> list[float]:
        # ttm PE = price at earnings announcement / ttm EPS
        quarterly_PE = []

        for quarter in self.quarterly_EPS:
            date = datetime.strptime(
                list(quarter.keys())[0],
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
                    try:
                        price = float(
                            dataForDate[const.ADJ_CLOSE][self.symbol]
                        )
                    except IndexError:
                        price = float(dataForDate[const.ADJ_CLOSE])
                except KeyError:
                    date = datetime.strptime(date, '%Y-%m-%d').date()
                    date = date + timedelta(days=1)
                    date = str(date)
                    attempts += 1

            eps = float(list(quarter.values())[0])
            try:
                quarterly_PE.append(price/eps)
            except ZeroDivisionError:
                quarterly_PE.append(0)
        return quarterly_PE

    def set_variables(self, quarterly_EPS: list[dict] = None) -> list[dict]:
        if (quarterly_EPS is not None):
            self.quarterly_EPS = quarterly_EPS
        else:
            self.quarterly_EPS = self.retriever.retrieve_quarterly_EPS()
