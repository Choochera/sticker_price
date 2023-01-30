from forex_python.converter import CurrencyRates
import Source.Fact_Parser.IFact_Parser as IFP
import Source.constants as const
import Source.Exceptions.DataRetrievalException as DRE
import json
from datetime import datetime


class IFRS_Fact_Parser(IFP.IFact_Parser):

    def __init__(self, symbol: str, facts: dict):
        self.symbol = symbol
        self.c = CurrencyRates()
        self.facts = facts[const.FACTS]

    def retrieve_quarterly_shareholder_equity(self) -> list[dict]:
        try:
            data = self.facts[const.IFRS][const.UPPER_EQUITY]
        except KeyError:
            with open(
                'Errors/DRE_EQUITY_%s.json' % self.symbol,
                const.WRITE
            ) as file:
                json.dump(self.facts, file)
            raise DRE.DataRetrievalException(const.EQUITY)
        currency = list(data[const.UNITS].keys())[0]
        qrtly_shareholder_equity = []
        for i in range(len(data[const.UNITS][currency])):
            amount = float(data[const.UNITS][currency][i][const.VAL])
            amount = self.c.convert(currency, const.USD, amount)
            val = {
                data[const.UNITS][currency][i][const.END]: amount
            }
            qrtly_shareholder_equity.append(val)

        return qrtly_shareholder_equity

    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        try:
            data = self.facts[const.IFRS][const.NUMBER_OUTSTANDING]
        except KeyError:
            with open(
                'Errors/DRE_OUTSTANDING_SHARES_%s.json' % self.symbol,
                const.WRITE
            ) as file:
                json.dump(self.facts, file)
            raise DRE.DataRetrievalException(
                const.OUTSTANDING_SHARES
            )
        qrtly_outstanding_shares = []
        for i in range(len(data[const.UNITS][const.SHARES])):
            amount = float(data[const.UNITS][const.SHARES][i][const.VAL])
            val = {
                data[const.UNITS][const.SHARES][i][const.END]: amount,
            }
            qrtly_outstanding_shares.append(val)
        return qrtly_outstanding_shares

    def retrieve_quarterly_EPS(self) -> list[dict]:
        try:
            data = self.facts[const.IFRS][const.E_L_PER_SHARE]
        except KeyError:
            try:
                data = self.facts[const.IFRS][const.B_D_E_L_PER_SHARE]
            except KeyError:
                with open(
                    'Errors/DRE_EPS_%s.json' % self.symbol,
                    const.WRITE
                ) as file:
                    json.dump(self.facts, file)
                raise DRE.DataRetrievalException(const.EPS)
        key = list(data[const.UNITS].keys())[0]
        currency = key.replace(const.SLASH_SHARES, const.EMPTY)

        quarterly_EPS = []
        period_end_dates: list[str] = []
        for period in data[const.UNITS][key]:
            try:
                if (
                    period[const.END] not in period_end_dates and
                    days_between(
                        period[const.START],
                        period[const.END]
                    ) < 105
                ):
                    amount = float(period[const.VAL])
                    amount = self.c.convert(currency, const.USD, amount)
                    val = {
                        period[const.END]: amount
                    }
                    quarterly_EPS.append(val)
                    period_end_dates.append(period[const.END])
            except KeyError:
                # Skip values without frame
                None

        return quarterly_EPS

    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        ttm_revenue: float = 0
        qrtly_revenue = []
        # Calculate ttm revenue total by adding reported
        # revenues from last 4 quarters
        try:
            data = self.facts[const.GROSS_PROFIT]
        except KeyError:
            try:
                data = self.facts[const.REVENUE]
            except KeyError:
                print('Could not retrieve benchmark ratio price'
                      'for symbol: ' + self.symbol)
                return 0

        currency = list(data[const.UNITS].keys())[0]
        for period in data[const.UNITS][currency]:
            amount = float(period[const.VAL])
            amount = self.c.convert(currency, const.USD, amount)
            try:
                if 'Q' in period[const.FRAME]:
                    qrtly_revenue.append(amount)
            except KeyError:
                # Skip values without frame
                None

        try:
            shares_outstanding = self.facts[const.NUMBER_OUTSTANDING]
        except KeyError:
            print('Could not retrieve benchmark ratio'
                  'price for symbol: ' + self.symbol)
            return 0

        shares_outstanding = self.retrieve_quarterly_outstanding_shares()
        shares_outstanding = list(
            shares_outstanding[len(shares_outstanding) - 1].values()
        )[0]
        ttm_revenue = sum(qrtly_revenue[-4:])

        # Equation for price based on provided market benchmark
        # = (revenue / shares outstanding) * benchmark price-sales ratio
        return round(ttm_revenue / float(shares_outstanding), 3) * benchmark


def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)
