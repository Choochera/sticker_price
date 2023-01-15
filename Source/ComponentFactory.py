import Source.Helper.Helper as Helper
import Source.Helper.IHelper as IHelper
import Source.Data_Retriever.Data_Retriever as DR
import Source.Data_Retriever.IData_Retriever as IDR
import Source.Data_Calculator.Data_Calculator as DC
import Source.Data_Calculator.IData_Calculator as IDC
import Source.Price_Check_Worker.Price_Check_Worker as PCW
import Source.Price_Check_Worker.IPrice_Check_Worker as IPCW
import Source.Fact_Parser.IFact_Parser as IFP
import Source.Fact_Parser.GAAP_Fact_Parser as GAAP
import Source.Fact_Parser.IFRS_Fact_Parser as IFRS
import Source.constants as const
import Source.Exceptions.InsufficientDataException as IDE


class ComponentFactory():

    def __init__(self):
        None

    def getHelperObject() -> IHelper.IHelper:
        return Helper.helper()

    def getDataRetrieverObject(
            symbol: str,
            facts: dict
            ) -> IDR.IData_Retriever:
        return DR.dataRetriever(
            symbol,
            facts
        )

    def getDataCalculatorObject(
            symbol: str,
            h_data: dict,
            facts: dict
            ) -> IDC.IData_Calculator:
        return DC.dataCalculator(
            symbol,
            h_data,
            facts[symbol]
        )

    def getPriceCheckWorker(
            threadID,
            name,
            counter,
            symbols: list[str],
            h_data: dict,
            facts: dict
            ) -> IPCW.IPrice_Check_Worker:
        return PCW.priceCheckWorker(
            threadID,
            name,
            counter,
            symbols,
            h_data,
            facts
        )

    def getFactParserObject(
            symbol: str,
            facts: dict
            ) -> IFP.IFact_Parser:
        if (const.GAAP in facts[const.FACTS].keys()):
            return GAAP.GAAP_Fact_Parser(
                symbol,
                facts
            )
        if (const.IFRS in facts[const.FACTS].keys()):
            return IFRS.IFRS_Fact_Parser(
                symbol,
                facts
            )
        raise IDE.InsufficientDataException(const.NO_FACTS)
