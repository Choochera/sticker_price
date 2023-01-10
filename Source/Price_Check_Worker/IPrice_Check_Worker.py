from abc import ABC, abstractmethod

class IPrice_Check_Worker(ABC):

    def __init__(self):
        None

    @abstractmethod
    def checkIsOnSale(self, symbol: str, priceData: dict) -> None:
        pass
