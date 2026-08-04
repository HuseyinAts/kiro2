"""
CQRS Base Interfaces for KIRO2 (August 2026 Ultra Standard)
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any
from pydantic import BaseModel

# Types
TResponse = TypeVar('TResponse')
TCommand = TypeVar('TCommand', bound='Command')
TQuery = TypeVar('TQuery', bound='Query')

class Command(BaseModel, ABC):
    """
    Base Command: State mutations, side effects (Write operations)
    """
    pass

class Query(BaseModel, ABC):
    """
    Base Query: Fetching data, no side effects (Read operations)
    """
    pass

class CommandHandler(ABC, Generic[TCommand, TResponse]):
    """
    Base Command Handler
    """
    @abstractmethod
    async def handle(self, command: TCommand) -> TResponse:
        pass

class QueryHandler(ABC, Generic[TQuery, TResponse]):
    """
    Base Query Handler
    """
    @abstractmethod
    async def handle(self, query: TQuery) -> TResponse:
        pass
