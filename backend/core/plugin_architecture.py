"""
Plugin Architecture for AI Agents
Enables easy addition of new agents without modifying core code
"""

import asyncio
import importlib
import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Agent capabilities"""

    TEACHING = "teaching"
    ASSESSMENT = "assessment"
    TUTORING = "tutoring"
    CONTENT_GENERATION = "content_generation"
    PROBLEM_SOLVING = "problem_solving"
    LANGUAGE_LEARNING = "language_learning"
    CODING_ASSISTANCE = "coding_assistance"
    RESEARCH = "research"
    GUIDANCE = "guidance"


@dataclass
class AgentManifest:
    """Agent plugin manifest"""

    name: str
    version: str
    description: str
    author: str
    capabilities: list[AgentCapability]
    supported_languages: list[str]
    supported_subjects: list[str]
    configuration: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    entry_point: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentProviderManifest:
    """Content provider manifest"""

    name: str
    version: str
    description: str
    content_types: list[str]
    supported_formats: list[str]
    api_endpoint: str | None = None
    local_path: str | None = None
    authentication: dict[str, Any] = field(default_factory=dict)
    rate_limits: dict[str, Any] = field(default_factory=dict)


class BaseAgentPlugin(ABC):
    """Base class for all agent plugins"""

    def __init__(self, manifest: AgentManifest):
        self.manifest = manifest
        self.initialized = False
        self.context_manager = None
        self.content_generator = None
        self.analytics = None

    @abstractmethod
    async def initialize(self, context_manager, content_generator, analytics):
        """Initialize the agent with core services"""
        self.context_manager = context_manager
        self.content_generator = content_generator
        self.analytics = analytics
        self.initialized = True

    @abstractmethod
    async def process_message(
        self, message: str, session_id: str, context: dict[str, Any] | None = None
    ) -> str:
        """Process a message and return response"""

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """Return list of agent capabilities"""

    @abstractmethod
    async def shutdown(self):
        """Cleanup resources"""

    async def validate_input(self, message: str) -> bool:
        """Validate input message"""
        if not message or len(message) > 10000:
            return False
        return True

    async def handle_error(self, error: Exception) -> str:
        """Handle errors gracefully"""
        logger.error(f"Agent {self.manifest.name} error: {error}")
        return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."


class ContentProvider(ABC):
    """Base class for content providers"""

    def __init__(self, manifest: ContentProviderManifest):
        self.manifest = manifest
        self.cache = {}

    @abstractmethod
    async def get_content(
        self,
        content_id: str,
        content_type: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get content by ID and type"""

    @abstractmethod
    async def search_content(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search for content"""

    @abstractmethod
    async def create_content(self, content_type: str, data: dict[str, Any]) -> str:
        """Create new content"""

    @abstractmethod
    async def update_content(self, content_id: str, updates: dict[str, Any]) -> bool:
        """Update existing content"""


class PluginLoader:
    """Loads and manages plugins"""

    def __init__(self, plugins_dir: str = "backend/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.agents: dict[str, BaseAgentPlugin] = {}
        self.content_providers: dict[str, ContentProvider] = {}
        self.manifests: dict[str, AgentManifest] = {}

    def discover_plugins(self) -> list[str]:
        """Discover available plugins"""
        discovered = []

        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return discovered

        # Look for manifest files
        for manifest_file in self.plugins_dir.glob("*/manifest.yaml"):
            plugin_name = manifest_file.parent.name
            discovered.append(plugin_name)
            logger.info(f"Discovered plugin: {plugin_name}")

        return discovered

    async def load_agent_plugin(self, plugin_name: str) -> BaseAgentPlugin | None:
        """Load an agent plugin"""
        try:
            # Load manifest
            manifest_path = self.plugins_dir / plugin_name / "manifest.yaml"
            if not manifest_path.exists():
                logger.error(f"Manifest not found for plugin: {plugin_name}")
                return None

            with open(manifest_path, encoding="utf-8") as f:
                manifest_data = yaml.safe_load(f)

            manifest = AgentManifest(**manifest_data)
            self.manifests[plugin_name] = manifest

            # Load plugin module
            module_path = f"backend.plugins.{plugin_name}.{manifest.entry_point}"
            module = importlib.import_module(module_path)

            # Find agent class
            agent_class = None
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseAgentPlugin)
                    and obj != BaseAgentPlugin
                ):
                    agent_class = obj
                    break

            if not agent_class:
                logger.error(f"No agent class found in plugin: {plugin_name}")
                return None

            # Create agent instance
            agent = agent_class(manifest)
            self.agents[plugin_name] = agent

            logger.info(f"Loaded agent plugin: {plugin_name}")
            return agent

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return None

    async def load_content_provider(self, provider_name: str) -> ContentProvider | None:
        """Load a content provider plugin"""
        try:
            # Load manifest
            manifest_path = self.plugins_dir / provider_name / "provider_manifest.yaml"
            if not manifest_path.exists():
                logger.error(f"Provider manifest not found: {provider_name}")
                return None

            with open(manifest_path, encoding="utf-8") as f:
                manifest_data = yaml.safe_load(f)

            manifest = ContentProviderManifest(**manifest_data)

            # Load provider module
            module_path = f"backend.plugins.{provider_name}.provider"
            module = importlib.import_module(module_path)

            # Find provider class
            provider_class = None
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, ContentProvider)
                    and obj != ContentProvider
                ):
                    provider_class = obj
                    break

            if not provider_class:
                logger.error(f"No provider class found: {provider_name}")
                return None

            # Create provider instance
            provider = provider_class(manifest)
            self.content_providers[provider_name] = provider

            logger.info(f"Loaded content provider: {provider_name}")
            return provider

        except Exception as e:
            logger.error(f"Error loading provider {provider_name}: {e}")
            return None

    def get_agent(self, agent_name: str) -> BaseAgentPlugin | None:
        """Get loaded agent by name"""
        return self.agents.get(agent_name)

    def get_content_provider(self, provider_name: str) -> ContentProvider | None:
        """Get loaded content provider by name"""
        return self.content_providers.get(provider_name)

    def list_agents(self) -> list[dict[str, Any]]:
        """List all loaded agents"""
        agents_list = []
        for name, agent in self.agents.items():
            agents_list.append(
                {
                    "name": name,
                    "version": agent.manifest.version,
                    "description": agent.manifest.description,
                    "capabilities": [c.value for c in agent.manifest.capabilities],
                    "initialized": agent.initialized,
                }
            )
        return agents_list

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name in self.agents:
            agent = self.agents[plugin_name]
            await agent.shutdown()
            del self.agents[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        return False


class AgentRegistry:
    """Central registry for all agents"""

    def __init__(self):
        self.registry: dict[str, dict[str, Any]] = {}
        self.capability_map: dict[AgentCapability, list[str]] = {}
        self.subject_map: dict[str, list[str]] = {}

    def register_agent(
        self, name: str, agent: BaseAgentPlugin, manifest: AgentManifest
    ):
        """Register an agent"""
        self.registry[name] = {
            "agent": agent,
            "manifest": manifest,
            "registered_at": asyncio.get_event_loop().time(),
        }

        # Update capability mapping
        for capability in manifest.capabilities:
            if capability not in self.capability_map:
                self.capability_map[capability] = []
            self.capability_map[capability].append(name)

        # Update subject mapping
        for subject in manifest.supported_subjects:
            if subject not in self.subject_map:
                self.subject_map[subject] = []
            self.subject_map[subject].append(name)

        logger.info(f"Registered agent: {name}")

    def get_agent_by_capability(
        self, capability: AgentCapability
    ) -> BaseAgentPlugin | None:
        """Get best agent for a capability"""
        agent_names = self.capability_map.get(capability, [])
        if not agent_names:
            return None

        # Return first available agent (could implement scoring)
        for name in agent_names:
            if name in self.registry:
                return self.registry[name]["agent"]

        return None

    def get_agent_by_subject(self, subject: str) -> BaseAgentPlugin | None:
        """Get best agent for a subject"""
        agent_names = self.subject_map.get(subject, [])
        if not agent_names:
            return None

        # Return first available agent
        for name in agent_names:
            if name in self.registry:
                return self.registry[name]["agent"]

        return None

    def get_all_agents(self) -> list[BaseAgentPlugin]:
        """Get all registered agents"""
        return [entry["agent"] for entry in self.registry.values()]

    def unregister_agent(self, name: str) -> bool:
        """Unregister an agent"""
        if name not in self.registry:
            return False

        manifest = self.registry[name]["manifest"]

        # Remove from capability map
        for capability in manifest.capabilities:
            if capability in self.capability_map:
                self.capability_map[capability].remove(name)

        # Remove from subject map
        for subject in manifest.supported_subjects:
            if subject in self.subject_map:
                self.subject_map[subject].remove(name)

        del self.registry[name]
        logger.info(f"Unregistered agent: {name}")
        return True


class AgentOrchestrator:
    """Orchestrates multiple agents for complex tasks"""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.task_queue = asyncio.Queue()
        self.results_cache = {}

    async def process_complex_request(
        self, request: str, session_id: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Process request using multiple agents if needed"""

        # Analyze request to determine required capabilities
        required_capabilities = self._analyze_request(request)

        # Get agents for each capability
        agents = []
        for capability in required_capabilities:
            agent = self.registry.get_agent_by_capability(capability)
            if agent:
                agents.append((capability, agent))

        if not agents:
            return {"success": False, "error": "No suitable agents found"}

        # Process with agents (parallel or sequential based on dependencies)
        results = {}

        if self._has_dependencies(required_capabilities):
            # Sequential processing
            for capability, agent in agents:
                result = await agent.process_message(request, session_id, context)
                results[capability.value] = result
                # Update context with result for next agent
                if context is None:
                    context = {}
                context[f"previous_{capability.value}"] = result
        else:
            # Parallel processing
            tasks = []
            for capability, agent in agents:
                task = agent.process_message(request, session_id, context)
                tasks.append((capability.value, task))

            # Wait for all tasks
            for capability_name, task in tasks:
                result = await task
                results[capability_name] = result

        # Combine results
        combined_result = self._combine_results(results, required_capabilities)

        return {
            "success": True,
            "results": results,
            "combined": combined_result,
            "agents_used": [
                name
                for _, agent in agents
                for name, entry in self.registry.registry.items()
                if entry["agent"] == agent
            ],
        }

    def _analyze_request(self, request: str) -> list[AgentCapability]:
        """Analyze request to determine required capabilities"""
        capabilities = []

        # Simple keyword-based analysis (could use NLP)
        keyword_map = {
            AgentCapability.TEACHING: ["öğret", "anlat", "açıkla"],
            AgentCapability.ASSESSMENT: ["sınav", "test", "değerlendir"],
            AgentCapability.PROBLEM_SOLVING: ["çöz", "problem", "hesapla"],
            AgentCapability.TUTORING: ["yardım", "destek", "rehber"],
        }

        request_lower = request.lower()
        for capability, keywords in keyword_map.items():
            if any(keyword in request_lower for keyword in keywords):
                capabilities.append(capability)

        # Default to teaching if no specific capability found
        if not capabilities:
            capabilities.append(AgentCapability.TEACHING)

        return capabilities

    def _has_dependencies(self, capabilities: list[AgentCapability]) -> bool:
        """Check if capabilities have dependencies"""
        # Define dependency rules
        dependencies = {
            AgentCapability.ASSESSMENT: [AgentCapability.TEACHING],
            AgentCapability.PROBLEM_SOLVING: [AgentCapability.TEACHING],
        }

        for capability in capabilities:
            if capability in dependencies:
                for dep in dependencies[capability]:
                    if dep in capabilities:
                        return True

        return False

    def _combine_results(
        self, results: dict[str, str], capabilities: list[AgentCapability]
    ) -> str:
        """Combine results from multiple agents"""
        if len(results) == 1:
            return list(results.values())[0]

        # Combine based on capability priority
        priority_order = [
            AgentCapability.TEACHING,
            AgentCapability.PROBLEM_SOLVING,
            AgentCapability.ASSESSMENT,
            AgentCapability.TUTORING,
        ]

        combined = []
        for capability in priority_order:
            if capability.value in results:
                combined.append(results[capability.value])

        return "\\n\\n".join(combined)


# Example custom agent plugin implementation
class MathTeacherPlugin(BaseAgentPlugin):
    """Example math teacher agent plugin"""

    async def initialize(self, context_manager, content_generator, analytics):
        await super().initialize(context_manager, content_generator, analytics)
        # Additional initialization
        self.topics = ["algebra", "geometry", "calculus"]

    async def process_message(
        self, message: str, session_id: str, context: dict[str, Any] | None = None
    ) -> str:
        """Process math-related questions"""

        if not await self.validate_input(message):
            return "Geçersiz giriş"

        try:
            # Get session context
            session = await self.context_manager.get_session(session_id)

            # Generate personalized math content
            student_profile = {
                "student_id": session.student_id if session else "unknown",
                "learning_style": context.get("learning_style", "visual"),
                "difficulty_level": context.get("difficulty", "medium"),
            }

            # Use content generator
            from core.dynamic_content_generator import ContentType

            content = await self.content_generator.generate_content(
                topic="matematik",
                content_type=ContentType.EXPLANATION,
                student_profile=student_profile,
                context=context,
            )

            return content.body

        except Exception as e:
            return await self.handle_error(e)

    async def get_capabilities(self) -> list[str]:
        return [cap.value for cap in self.manifest.capabilities]

    async def shutdown(self):
        # Cleanup resources
        pass


# Singleton instances
_plugin_loader = None
_agent_registry = None
_agent_orchestrator = None


def get_plugin_loader() -> PluginLoader:
    """Get or create plugin loader"""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader


def get_agent_registry() -> AgentRegistry:
    """Get or create agent registry"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


def get_agent_orchestrator() -> AgentOrchestrator:
    """Get or create agent orchestrator"""
    global _agent_orchestrator
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator(get_agent_registry())
    return _agent_orchestrator
