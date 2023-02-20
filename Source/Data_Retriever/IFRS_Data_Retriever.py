import Source.ComponentFactory as CF
import Source.Data_Retriever.IData_Retriever as IDR
import requests
import lxml.html as lh
import Source.constants as const
import Source.Exceptions.DataRetrievalException as DRE


class IFRS_Data_Retriever(IDR.IData_Retriever):

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
                const.UPPER_EQUITY
            ],
            taxonomyType=const.IFRS
        )

    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[
                const.NUMBER_OUTSTANDING
            ],
            deiFactsKeys=[const.E_COMMON_OUTSTANDING],
            taxonomyType=const.IFRS
        )

    def retrieve_quarterly_EPS(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.E_L_PER_SHARE, const.B_D_E_L_PER_SHARE],
            taxonomyType=const.IFRS,
        )

    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        try:
            data = self.parser.retrieve_quarterly_data(
                factsKeys=[
                    const.GROSS_PROFIT,
                    const.REVENUE
                ],
                taxonomyType=const.IFRS
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

    def retrieve_quarterly_long_term_debt(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.LONG_TERM_DEBT],
            taxonomyType=const.GAAP
        )

    def retrieve_long_term_debt_parts(self) -> list[list[dict]]:
        parts: list[list[dict]] = []
        keys = [
            const.LONG_TERM_DEBT_TTM,
            const.LONG_TERM_DEBT_YEAR_TWO,
            const.LONG_TERM_DEBT_YEAR_THREE,
            const.LONG_TERM_DEBT_YEAR_FOUR,
            const.LONG_TERM_DEBT_YEAR_FIVE
        ]
        for key in keys:
            try:
                parts.append(self.parser.retrieve_quarterly_data(
                    factsKeys=[key],
                    taxonomyType=const.IFRS
                ))
            except Exception:
                pass
        return parts
