from abc import ABC, abstractmethod


class IData_Calculator(ABC):

    def __init__(self):
        None

    @abstractmethod
    def calculate_sticker_price_data(self) -> dict:
        pass
