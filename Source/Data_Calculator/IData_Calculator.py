from abc import ABC, abstractmethod

class IData_Calculator(ABC):

    def __init__(self):
        None

    @abstractmethod
    def calculate_quarterly_PE(self) -> list[float]:
        pass

    @abstractmethod
    def calculate_quarterly_BVPS(self) -> list[dict]:
        pass

    @abstractmethod
    def calculate_sticker_price(self, trailing_years: int, equity_growth_rate: float, annual_PE: list, annual_EPS: list) -> dict:
        pass

    @abstractmethod
    def append_price_values(self, priceData: dict, additions: dict) -> None:
        pass

    @abstractmethod
    def calculate_sticker_price_data(self) -> dict:
        pass

