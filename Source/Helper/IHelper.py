from abc import ABC, abstractmethod
import asyncio


class IHelper(ABC):

    def __init__(self):
        None

    @abstractmethod
    def retrieve_facts(self, symbol: str) -> dict:
        pass

    @abstractmethod
    async def retrieve_bulk_facts(
            self,
            symbols: list[str],
            loop: asyncio.AbstractEventLoop) -> dict:
        pass

    @abstractmethod
    def retrieve_stock_list(self, stocks: list[str]) -> None:
        pass

    @abstractmethod
    def add_padding_to_collection(dict_list: dict) -> None:
        pass

    @abstractmethod
    def write_processed_symbols(symbol: str, symbols: list[str]) -> None:
        pass
