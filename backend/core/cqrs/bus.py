"""
CQRS Bus Implementation for KIRO2 (August 2026 Ultra Standard)
"""
import logging
import time
from typing import Type, TypeVar, Any
from .base import Command, Query, CommandHandler, QueryHandler

logger = logging.getLogger(__name__)

TCommand = TypeVar('TCommand', bound=Command)
TQuery = TypeVar('TQuery', bound=Query)
TResponse = TypeVar('TResponse')

class CommandBus:
    """
    Routes commands to their respective handlers.
    Includes telemetry and execution tracking.
    """
    def __init__(self):
        self._handlers: dict[Type[Command], CommandHandler] = {}

    def register(self, command_type: Type[Command], handler: CommandHandler):
        self._handlers[command_type] = handler
        logger.info(f"Registered CommandHandler: {handler.__class__.__name__} for {command_type.__name__}")

    async def execute(self, command: TCommand) -> Any:
        command_type = type(command)
        handler = self._handlers.get(command_type)
        if not handler:
            raise ValueError(f"No handler registered for command: {command_type.__name__}")
        
        start_time = time.perf_counter()
        try:
            logger.debug(f"Executing command: {command_type.__name__}")
            result = await handler.handle(command)
            duration = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Command {command_type.__name__} executed successfully in {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(f"Command {command_type.__name__} failed after {duration:.2f}ms: {e}", exc_info=True)
            raise


class QueryBus:
    """
    Routes queries to their respective handlers.
    Includes telemetry and execution tracking.
    """
    def __init__(self):
        self._handlers: dict[Type[Query], QueryHandler] = {}

    def register(self, query_type: Type[Query], handler: QueryHandler):
        self._handlers[query_type] = handler
        logger.info(f"Registered QueryHandler: {handler.__class__.__name__} for {query_type.__name__}")

    async def execute(self, query: TQuery) -> Any:
        query_type = type(query)
        handler = self._handlers.get(query_type)
        if not handler:
            raise ValueError(f"No handler registered for query: {query_type.__name__}")
        
        start_time = time.perf_counter()
        try:
            logger.debug(f"Executing query: {query_type.__name__}")
            result = await handler.handle(query)
            duration = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Query {query_type.__name__} executed successfully in {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(f"Query {query_type.__name__} failed after {duration:.2f}ms: {e}", exc_info=True)
            raise


# Global singleton instances for easy dependency injection
command_bus = CommandBus()
query_bus = QueryBus()

def get_command_bus() -> CommandBus:
    return command_bus

def get_query_bus() -> QueryBus:
    return query_bus
