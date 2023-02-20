
import Source.ComponentFactory as CF
import Source.Exceptions.DataRetrievalException as DRE
import Source.Data_Calculator.Functions.IData_Calculator_Function as IDC
import Source.constants as const
import Source.Exceptions.InsufficientDataException as IDE


class BVPS_Calculator(IDC.IData_Calculator_Function):

    def __init__(
        self,
        symbol: str,
        facts: dict
    ):
        super().__init__(symbol, facts)
        self.quarterly_shareholder_equity = None,
        self.quarterly_outstanding_shares = None

        try:
            self.retriever = CF.ComponentFactory.getDataRetrieverObject(
                self.symbol,
                self.facts
            )
            self.helper = CF.ComponentFactory.getHelperObject()
        except Exception as e:
            raise e

    def calculate(self) -> list[float]:
        quarterly_BVPS = []
        last_share_value = -1
        processedDates = []
        self.quarterly_outstanding_shares.reverse()
        for equity in self.quarterly_shareholder_equity:
            if (list(equity.keys())[0] not in str(processedDates)):
                for shares in self.quarterly_outstanding_shares:
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

    def set_variables(self) -> None:
        try:
            a = self.retriever.retrieve_quarterly_shareholder_equity()
        except DRE.DataRetrievalException:
            self.helper.write_error_file(
                self.symbol,
                const.EQUITY,
                const.DRE,
                self.facts
            )
        try:
            b = self.retriever.retrieve_quarterly_outstanding_shares()
        except DRE.DataRetrievalException:
            self.helper.write_error_file(
                self.symbol,
                const.OUTSTANDING_SHARES,
                const.DRE,
                self.facts
            )

        self.quarterly_shareholder_equity = a
        self.quarterly_outstanding_shares = b

    def annualize(self, quarterly_BVPS) -> tuple[list[float], list[float]]:
        if (len(quarterly_BVPS) < 40):
            raise IDE.InsufficientDataException(const.QRTLY_BVPS)
        annual_BVPS: list[float] = []
        first_quarter: list[float] = []
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
        return [first_quarter, annual_BVPS]
