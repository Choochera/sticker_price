import Source.ComponentFactory as CF
import Data_Retriever.IData_Retriever
import Data_Retriever.Fact_Parser_Factory.Fact_Parser_Factory as parserFactory

class dataRetriever(Data_Retriever.IData_Retriever.IData_Retriever):

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.helper = CF.ComponentFactory.getHelperObject()
        try:
            self.facts = self.helper.retrieve_facts(symbol)
        except Exception as e:
            raise e
        self.parser = parserFactory.FactParserFactory.getFactParserObject(self.symbol, self.facts)

    def retrieve_quarterly_shareholder_equity(self) -> list[dict]:
        return self.parser.retrieve_quarterly_shareholder_equity()

    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        return self.parser.retrieve_quarterly_outstanding_shares()

    def retrieve_quarterly_EPS(self) -> list[dict]:
        return self.parser.retrieve_quarterly_EPS()

    def retrieve_fy_growth_estimate(self) -> float:
        return self.helper.retrieve_fy_growth_estimate(self.symbol)

    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        return self.parser.retrieve_benchmark_ratio_price(benchmark)