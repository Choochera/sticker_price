from abc import ABC, abstractmethod


class IData_Calculator_Function(ABC):

    def __init__(self, symbol: str, facts: dict):
        self.symbol = symbol
        self.facts = facts

    @abstractmethod
    def calculate(self) -> list[float] or dict:
        pass

    @abstractmethod
    def set_variables(self) -> None:
        pass

    @abstractmethod
    def annualize(
        self,
        quarterly_data: list[dict]
    ) -> list[float] or tuple[list[float], list[float]]:
        pass
