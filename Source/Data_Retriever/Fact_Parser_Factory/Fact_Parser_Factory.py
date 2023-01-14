import Source.Data_Retriever.Fact_Parser_Factory.Fact_Parser.IFact_Parser as IFP
import Source.Data_Retriever.Fact_Parser_Factory.Fact_Parser.GAAP_Fact_Parser as GFP
import Source.Data_Retriever.Fact_Parser_Factory.Fact_Parser.IFRS_Fact_Parser as IFRS_FP

class FactParserFactory():
    
    def __init__(self):
        None

    def getFactParserObject(symbol: str, facts: dict) -> IFP.IFact_Parser:
        if ('us-gaap' in facts['facts'].keys()):
            return GFP.GAAP_Fact_Parser(symbol, facts)
        if ('ifrs-full' in facts['facts'].keys()):
            return IFRS_FP.IFRS_Fact_Parser(symbol, facts)
        raise Exception("Error: Insufficient facts data")
