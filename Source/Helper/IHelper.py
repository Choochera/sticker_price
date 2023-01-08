from abc import ABC, abstractmethod
import requests

class IHelper(ABC):

    def __init__(self):
        None

    @abstractmethod
    def send_SEC_api_request(self, symbol: str, element: str) -> requests.Request:
        pass

    @abstractmethod
    def retrieve_facts(self, symbol: str) -> requests.Response:
        pass

    @abstractmethod
    def retrieve_fy_growth_estimate(self, symbol: str) -> float:
        pass