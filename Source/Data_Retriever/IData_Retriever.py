from abc import ABC, abstractmethod

class IData_Retriever(ABC):

    def __init__(self):
        None

    @abstractmethod
    def retrieve_quarterly_shareholder_equity(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_quarterly_EPS(self) -> list[dict]:
        pass

    @abstractmethod
    def retrieve_fy_growth_estimate(self) -> float:
        pass

    @abstractmethod
    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        pass
