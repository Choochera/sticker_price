import Source.ComponentFactory as CF
import Source.Data_Retriever.IData_Retriever as IDR
import Source.Data_Retriever.Fact_Parser_Factory.Fact_Parser_Factory as PF
import requests
import lxml.html as lh

class dataRetriever(IDR.IData_Retriever):

    def __init__(self, symbol: str, facts: dict):
        self.symbol = symbol
        self.helper = CF.ComponentFactory.getHelperObject()
        self.facts = facts
        self.parser = PF.FactParserFactory.getFactParserObject(self.symbol, self.facts)

    def retrieve_quarterly_shareholder_equity(self) -> list[dict]:
        return self.parser.retrieve_quarterly_shareholder_equity()

    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        return self.parser.retrieve_quarterly_outstanding_shares()

    def retrieve_quarterly_EPS(self) -> list[dict]:
        return self.parser.retrieve_quarterly_EPS()

    def retrieve_fy_growth_estimate(self) -> float:
        url = "https://www.zacks.com/stock/quote/" + self.symbol + "/detailed-estimates"
        try:
            page = requests.get(url, headers = {'User-Agent' : '008'})
            doc = lh.fromstring(page.content)
        except requests.exceptions.HTTPError as hError:
            raise Exception(str("Http Error:", hError))
        except requests.exceptions.ConnectionError as cError:
            raise Exception(str("Error Connecting:", cError))
        except requests.exceptions.Timeout as tError:
            raise Exception(str("Timeout Error:", tError))
        except requests.exceptions.RequestException as rError:
            raise Exception(str("Other Error:", rError))

        td_elements = doc.xpath('//td')

        for i in range(len(td_elements)):
            if(td_elements[i].text_content() == 'Next 5 Years'):
                return td_elements[i + 1].text_content() 
        
        return -1

    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        return self.parser.retrieve_benchmark_ratio_price(benchmark)