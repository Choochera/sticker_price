from abc import ABC, abstractmethod


class IFact_Parser(ABC):

    def __init__(self):
        None

    @abstractmethod
    def retrieve_quarterly_data(
        self,
        factsKeys: list[str],
        taxonomyType: str,
        deiFactsKeys: list[str],
        hasStartDate: bool
    ) -> list[dict]:
        pass
