import Source.ComponentFactory as CF
import Source.Data_Retriever.IData_Retriever as IDR
import requests
import lxml.html as lh
import Source.constants as const
import Source.Exceptions.DataRetrievalException as DRE


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
            taxonomyType=const.GAAP,
            hasStartDate=False
        )

    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[
                const.COMMON_SHARES_OUTSTANDING,
                const.COMMON_SHARES_ISSUED
            ],
            deiFactsKeys=[const.E_COMMON_OUTSTANDING],
            taxonomyType=const.GAAP,
            hasStartDate=False
        )

    def retrieve_quarterly_EPS(self) -> list[dict]:
        return self.parser.retrieve_quarterly_data(
            factsKeys=[const.EPS_BASIC],
            taxonomyType=const.GAAP,
        )

    def retrieve_fy_growth_estimate(self) -> float:
        url = const.ZACKS_URL % self.symbol
        try:
            page = requests.get(
                url,
                headers={'User-Agent': const.USER_AGENT}
            )
            doc = lh.fromstring(page.content)
        except requests.exceptions.HTTPError as hError:
            raise DRE.DataRetrievalException(
                const.HTTP
            )
        except requests.exceptions.ConnectionError as cError:
            raise DRE.DataRetrievalException(
                const.CONNECTING
            )
        except requests.exceptions.Timeout as tError:
            raise DRE.DataRetrievalException(
                const.TIMEOUT
            )
        except requests.exceptions.RequestException as rError:
            raise DRE.DataRetrievalException(
                const.REQUEST
            )

        td_elements = doc.xpath(const.TABLE_DATA)

        for i in range(len(td_elements)):
            if (td_elements[i].text_content() == const.NEXT_FIVE_YEARS):
                return td_elements[i + 1].text_content()

        return -1

    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        try:
            data = self.parser.retrieve_quarterly_data(factsKeys=[const.GROSS_PROFIT, const.REVENUES], taxonomyType=const.GAAP)
        except Exception:
            print('Could not retrieve benchmark'
                      'ratio price for symbol: ' + self.symbol)
            return 0
        
        qrtly_revenue = list(map(lambda quarter: quarter[list(quarter.keys())[0]], data))
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
