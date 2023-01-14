import Source.Helper.Helper as Helper
import Source.Helper.IHelper as IHelper
import Source.Data_Retriever.Data_Retriever as DR
import Source.Data_Retriever.IData_Retriever as IDR
import Source.Data_Calculator.Data_Calculator as DC
import Source.Data_Calculator.IData_Calculator as IDC
import Source.Price_Check_Worker.Price_Check_Worker as PCW
import Source.Price_Check_Worker.IPrice_Check_Worker as IPCW

class ComponentFactory():
    
    def __init__(self):
        None

    def getHelperObject() -> IHelper.IHelper:
        return Helper.helper()

    def getDataRetrieverObject(symbol: str, facts: dict) -> IDR.IData_Retriever:
        return DR.dataRetriever(symbol, facts)

    def getDataCalculatorObject(symbol: str, h_data: dict, facts: dict) -> IDC.IData_Calculator:
        return DC.dataCalculator(symbol, h_data, facts[symbol])

    def getPriceCheckWorker(threadID, name, counter, symbols: list[str], h_data: dict, facts: dict) -> IPCW.IPrice_Check_Worker:
        return PCW.priceCheckWorker(threadID, name, counter, symbols, h_data, facts)