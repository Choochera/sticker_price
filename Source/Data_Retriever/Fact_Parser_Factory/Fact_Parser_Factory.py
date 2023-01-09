import Data_Retriever.Fact_Parser_Factory.Fact_Parser.IFact_Parser as IFact_Parser
import Data_Retriever.Fact_Parser_Factory.Fact_Parser.GAAP_Fact_Parser as GAAP_Fact_Parser
import Data_Retriever.Fact_Parser_Factory.Fact_Parser.IFRS_Fact_Parser as IFRS_Fact_Parser

class FactParserFactory():
    
    def __init__(self):
        None

    def getFactParserObject(symbol: str, facts: dict) -> IFact_Parser.IFact_Parser:
        if ('us-gaap' in facts['facts'].keys()):
            return GAAP_Fact_Parser.GAAP_Fact_Parser(symbol, facts)
        if ('ifrs-full' in facts['facts'].keys()):
            return IFRS_Fact_Parser.IFRS_Fact_Parser(symbol, facts)
        raise Exception("Error: Insufficient facts data")
