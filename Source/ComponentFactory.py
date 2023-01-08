import sys, os
sys.path.extend([f'./{name}' for name in os.listdir(".") if os.path.isdir(name)])
import Helper.Helper
import Helper.IHelper
import Data_Retriever
import Data_Retriever.Data_Retriever
import Data_Calculator
import Data_Calculator.Data_Calculator

class ComponentFactory():
    
    def __init__(self):
        None

    def getHelperObject() -> Helper.IHelper.IHelper:
        return Helper.Helper.helper()

    def getDataRetrieverObject(symbol: str) -> Data_Retriever.IData_Retriever.IData_Retriever:
        return Data_Retriever.Data_Retriever.dataRetriever(symbol)

    def getDataCalculatorObject(symbol: str, h_data: dict) -> Data_Calculator.IData_Calculator.IData_Calculator:
        return Data_Calculator.Data_Calculator.dataCalculator(symbol, h_data)