from abc import ABC, abstractmethod
import requests
import lxml.html as lh
import Source.constants as const
import Source.Exceptions.DataRetrievalException as DRE


class IData_Retriever(ABC):

    def __init__(self):
        None

    @abstractmethod
    def retrieve_quarterly_shareholder_equity(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_quarterly_EPS(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        pass

    @abstractmethod
    def retrieve_quarterly_net_income(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_quarterly_long_term_debt(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_long_term_debt_parts(self) -> list[list[dict]]:
        pass

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
