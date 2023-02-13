import Source.Helper.Helper as Helper
import Source.Helper.IHelper as IHelper
import Source.Data_Retriever.GAAP_Data_Retriever as GAAP_DR
import Source.Data_Retriever.IFRS_Data_Retriever as IFRS_DR
import Source.Data_Retriever.IData_Retriever as IDR
import Source.Data_Calculator.Data_Calculator as DC
import Source.Data_Calculator.IData_Calculator as IDC
import Source.Price_Check_Worker.Price_Check_Worker as PCW
import Source.Price_Check_Worker.IPrice_Check_Worker as IPCW
import Source.Fact_Parser.IFact_Parser as IFP
import Source.Fact_Parser.Fact_Parser as FP
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
        if (const.GAAP in facts[const.FACTS].keys()):
            return GAAP_DR.GAAP_Data_Retriever(
                symbol,
                facts
            )
        if (const.IFRS in facts[const.FACTS].keys()):
            return IFRS_DR.IFRS_Data_Retriever(
                symbol,
                facts
            )
        raise IDE.InsufficientDataException(const.NO_FACTS)

    def getDataCalculatorObject(
            symbol: str,
            h_data: dict,
            facts: dict
            ) -> IDC.IData_Calculator:
        return DC.dataCalculator(
            symbol,
            h_data,
            facts
        )

    def getPriceCheckWorker(
            threadID,
            name,
            counter,
            symbols: list[str],
            h_data: dict,
            helper: IHelper.IHelper,
            facts: dict = None,
            ) -> IPCW.IPrice_Check_Worker:
        return PCW.priceCheckWorker(
            threadID,
            name,
            counter,
            symbols,
            h_data,
            facts,
            helper
        )

    def getFactParserObject(
            symbol: str,
            facts: dict
            ) -> IFP.IFact_Parser:
        return FP.Fact_Parser(
            symbol,
            facts
        )
