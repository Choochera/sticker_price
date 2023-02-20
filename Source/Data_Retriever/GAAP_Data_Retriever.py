import Source.ComponentFactory as CF
import Source.Data_Retriever.IData_Retriever as IDR
import Source.constants as const


class GAAP_Data_Retriever(IDR.IData_Retriever):

    def __init__(self, symbol: str, facts: dict):
        self.symbol = symbol
        self.facts = facts
        self.parser = CF.ComponentFactory.getFactParserObject(
            self.symbol,
            self.facts
        )

    def retrieve_quarterly_shareholder_equity(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[
                const.HOLDERS_EQUITY,
                const.L_AND_H_EQUITY
            ],
            taxonomyType=const.GAAP
        )

    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[
                const.COMMON_SHARES_OUTSTANDING,
                const.COMMON_SHARES_ISSUED,
                const.AVG_NUM_SHARES_OUTSTANDING
            ],
            deiFactsKeys=[const.E_COMMON_OUTSTANDING],
            taxonomyType=const.GAAP
        )

    def retrieve_quarterly_EPS(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[
                const.EPS_BASIC,
                const.NET_PER_OUTSTANDING_LPU
                ],
            taxonomyType=const.GAAP
        )

    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        try:
            data = self.parser.retrieve_quarterly_data(
                factsKeys=[
                    const.GROSS_PROFIT,
                    const.REVENUES
                ],
                taxonomyType=const.GAAP
            )
        except Exception:
            print('Could not retrieve benchmark'
                  'ratio price for symbol: ' + self.symbol)
            return 0

        qrtly_revenue = list(
            map(
                lambda quarter: quarter[list(quarter.keys())[0]],
                data
            )
        )
        shares_outstanding = self.retrieve_quarterly_outstanding_shares()
        shares_outstanding = list(
            shares_outstanding[len(shares_outstanding) - 1].values()
            )[0]
        ttm_revenue = sum(qrtly_revenue[-4:])

        # Equation for price based on provided market benchmark
        # = (revenue / shares outstanding) * benchmark price-sales ratio
        return round(ttm_revenue / float(shares_outstanding), 3) * benchmark

    def retrieve_quarterly_net_income(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.NET_INCOME_LOSS],
            taxonomyType=const.GAAP,
        )

    def retrieve_quarterly_total_debt(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.DEBT_CURRENT],
            taxonomyType=const.GAAP,
        )

    def retrieve_quarterly_total_assets(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.ASSETS],
            taxonomyType=const.GAAP
        )

    def retrieve_quarterly_total_cash(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.CASH_AT_CARRYING_VALUE],
            taxonomyType=const.GAAP
        )

    def retrieve_quarterly_long_term_debt(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.LONG_TERM_DEBT,
                       const.UNSECURED_LONG_TERM_DEBT],
            taxonomyType=const.GAAP
        )
