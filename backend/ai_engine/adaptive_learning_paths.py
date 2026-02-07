"""
Adaptive Learning Path Generator
AI-powered personalized learning path creation and optimization
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import networkx as nx
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class LearningPathType(Enum):
    """Types of learning paths"""

    SEQUENTIAL = "sequential"
    ADAPTIVE = "adaptive"
    REMEDIAL = "remedial"
    ACCELERATED = "accelerated"
    EXPLORATORY = "exploratory"
    EXAM_FOCUSED = "exam_focused"


class LearningNodeType(Enum):
    """Types of learning nodes"""

    CONCEPT = "concept"
    SKILL = "skill"
    ASSESSMENT = "assessment"
    PRACTICE = "practice"
    PROJECT = "project"
    REFLECTION = "reflection"


class MasteryLevel(Enum):
    """Mastery levels for learning objectives"""

    NOT_STARTED = 0
    BEGINNER = 1
    DEVELOPING = 2
    PROFICIENT = 3
    ADVANCED = 4
    EXPERT = 5


@dataclass
class LearningObjective:
    """Individual learning objective or concept"""

    objective_id: str
    title: str
    description: str
    subject: str
    topic: str

    # Hierarchy and relationships
    prerequisites: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    enables: List[str] = field(default_factory=list)  # What this enables
    related_concepts: List[str] = field(default_factory=list)

    # Learning characteristics
    estimated_time: int = 30  # minutes
    difficulty_level: float = 0.5  # 0-1
    cognitive_load: float = 0.5  # 0-1
    importance_weight: float = 1.0  # 0-1

    # Assessment criteria
    mastery_threshold: float = 0.8  # 0-1
    assessment_methods: List[str] = field(default_factory=list)

    # Personalization factors
    learning_styles: List[str] = field(
        default_factory=list
    )  # visual, auditory, kinesthetic
    preferred_modalities: List[str] = field(
        default_factory=list
    )  # video, text, interactive

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningNode:
    """Individual node in learning path"""

    node_id: str
    objective: LearningObjective
    node_type: LearningNodeType

    # Progress tracking
    current_mastery: MasteryLevel = MasteryLevel.NOT_STARTED
    mastery_score: float = 0.0  # 0-1
    attempts: int = 0
    time_spent: int = 0  # minutes

    # Scheduling
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    # Adaptive parameters
    difficulty_adjustment: float = 0.0  # -0.5 to +0.5
    repetition_count: int = 0
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None

    # Resources and activities
    resources: List[Dict[str, Any]] = field(default_factory=list)
    activities: List[Dict[str, Any]] = field(default_factory=list)
    assessments: List[Dict[str, Any]] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningPath:
    """Complete learning path for a student"""

    path_id: str
    student_id: str
    path_type: LearningPathType
    subject: str

    # Path metadata
    title: str
    description: str
    learning_goals: List[str]
    target_completion: datetime
    estimated_duration: int  # minutes

    # Path structure
    nodes: List[LearningNode]
    dependencies: Dict[str, List[str]]  # node_id -> [prerequisite_node_ids]
    alternative_paths: Dict[str, List[str]] = field(default_factory=dict)

    # Progress tracking
    overall_progress: float = 0.0  # 0-1
    nodes_completed: int = 0
    total_time_spent: int = 0  # minutes

    # Adaptive parameters
    difficulty_preference: float = 0.5  # 0-1
    pace_preference: float = 0.5  # 0-1 (slow to fast)
    learning_style_weights: Dict[str, float] = field(default_factory=dict)

    # Performance metrics
    average_mastery: float = 0.0
    struggle_points: List[str] = field(
        default_factory=list
    )  # node_ids where student struggled
    strength_areas: List[str] = field(default_factory=list)

    # Scheduling
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PathOptimizationContext:
    """Context for path optimization"""

    available_time: int  # minutes per week
    deadline: Optional[datetime] = None
    focus_areas: List[str] = field(default_factory=list)  # specific topics to emphasize
    avoid_areas: List[str] = field(default_factory=list)  # topics to minimize
    learning_style_preference: Optional[str] = None
    difficulty_tolerance: float = 0.5  # 0-1
    novelty_preference: float = 0.5  # 0-1 (familiar to novel)
    collaboration_preference: float = 0.5  # 0-1 (individual to collaborative)


class AdaptiveLearningPathGenerator:
    """AI-powered adaptive learning path generator"""

    def __init__(self):
        self.ready = False
        self.objective_database = {}
        self.learning_graph = nx.DiGraph()
        self.student_profiles = {}
        self.path_templates = {}

        # ML models for optimization
        self.clustering_model = None
        self.scaler = StandardScaler()

        # Optimization parameters
        self.optimization_weights = {
            "mastery_progression": 0.3,
            "time_efficiency": 0.2,
            "engagement": 0.2,
            "prerequisite_coverage": 0.15,
            "difficulty_appropriateness": 0.15,
        }

    async def initialize(self):
        """Initialize the learning path generator"""
        if self.ready:
            return

        logger.info("Initializing Adaptive Learning Path Generator...")

        try:
            # Load learning objectives and build knowledge graph
            await self._load_learning_objectives()
            await self._build_knowledge_graph()

            # Initialize ML models
            await self._initialize_ml_models()

            # Load path templates
            await self._load_path_templates()

            self.ready = True
            logger.info("Adaptive Learning Path Generator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize path generator: {e}")
            raise

    async def _load_learning_objectives(self):
        """Load learning objectives database"""
        # Sample learning objectives for Turkish education system
        objectives_data = [
            {
                "objective_id": "math_algebra_linear_eq",
                "title": "Doğrusal Denklemler",
                "description": "Tek bilinmeyenli doğrusal denklemleri çözme",
                "subject": "matematik",
                "topic": "cebir",
                "prerequisites": [],
                "estimated_time": 120,
                "difficulty_level": 0.3,
                "cognitive_load": 0.4,
                "importance_weight": 0.8,
            },
            {
                "objective_id": "math_algebra_quadratic_eq",
                "title": "İkinci Dereceden Denklemler",
                "description": "İkinci dereceden denklemleri çözme yöntemleri",
                "subject": "matematik",
                "topic": "cebir",
                "prerequisites": ["math_algebra_linear_eq"],
                "estimated_time": 180,
                "difficulty_level": 0.6,
                "cognitive_load": 0.7,
                "importance_weight": 0.9,
            },
            {
                "objective_id": "math_geometry_triangles",
                "title": "Üçgenler",
                "description": "Üçgen özellikleri ve çeşitleri",
                "subject": "matematik",
                "topic": "geometri",
                "prerequisites": [],
                "estimated_time": 150,
                "difficulty_level": 0.4,
                "cognitive_load": 0.5,
                "importance_weight": 0.7,
            },
            {
                "objective_id": "math_geometry_similarity",
                "title": "Benzerlik",
                "description": "Üçgenlerde benzerlik ve benzerlik kriterleri",
                "subject": "matematik",
                "topic": "geometri",
                "prerequisites": ["math_geometry_triangles"],
                "estimated_time": 200,
                "difficulty_level": 0.7,
                "cognitive_load": 0.8,
                "importance_weight": 0.8,
            },
            {
                "objective_id": "physics_mechanics_force",
                "title": "Kuvvet Kavramı",
                "description": "Kuvvet, kuvvetin özellikleri ve türleri",
                "subject": "fizik",
                "topic": "mekanik",
                "prerequisites": [],
                "estimated_time": 100,
                "difficulty_level": 0.4,
                "cognitive_load": 0.5,
                "importance_weight": 0.8,
            },
            {
                "objective_id": "physics_mechanics_newton_laws",
                "title": "Newton Kanunları",
                "description": "Newton'un hareket kanunları ve uygulamaları",
                "subject": "fizik",
                "topic": "mekanik",
                "prerequisites": ["physics_mechanics_force"],
                "estimated_time": 240,
                "difficulty_level": 0.8,
                "cognitive_load": 0.9,
                "importance_weight": 0.9,
            },
        ]

        # Convert to LearningObjective objects
        for obj_data in objectives_data:
            objective = LearningObjective(
                objective_id=obj_data["objective_id"],
                title=obj_data["title"],
                description=obj_data["description"],
                subject=obj_data["subject"],
                topic=obj_data["topic"],
                prerequisites=obj_data.get("prerequisites", []),
                estimated_time=obj_data["estimated_time"],
                difficulty_level=obj_data["difficulty_level"],
                cognitive_load=obj_data["cognitive_load"],
                importance_weight=obj_data["importance_weight"],
                learning_styles=["visual", "auditory"],
                preferred_modalities=["video", "interactive"],
                assessment_methods=["quiz", "practice"],
            )
            self.objective_database[objective.objective_id] = objective

    async def _build_knowledge_graph(self):
        """Build knowledge graph from learning objectives"""
        # Add nodes
        for obj_id, objective in self.objective_database.items():
            self.learning_graph.add_node(obj_id, objective=objective)

        # Add prerequisite edges
        for obj_id, objective in self.objective_database.items():
            for prereq in objective.prerequisites:
                if prereq in self.objective_database:
                    self.learning_graph.add_edge(
                        prereq, obj_id, relation="prerequisite"
                    )

        # Add related concept edges
        self._add_semantic_relationships()

    def _add_semantic_relationships(self):
        """Add semantic relationships between concepts"""
        # Group objectives by subject and topic
        subject_groups = {}
        for obj_id, objective in self.objective_database.items():
            key = f"{objective.subject}_{objective.topic}"
            if key not in subject_groups:
                subject_groups[key] = []
            subject_groups[key].append(obj_id)

        # Add weak relationships within topics
        for group in subject_groups.values():
            for i, obj1 in enumerate(group):
                for obj2 in group[i + 1 :]:
                    if not self.learning_graph.has_edge(
                        obj1, obj2
                    ) and not self.learning_graph.has_edge(obj2, obj1):
                        # Add bidirectional weak relationship
                        self.learning_graph.add_edge(
                            obj1, obj2, relation="related", weight=0.3
                        )
                        self.learning_graph.add_edge(
                            obj2, obj1, relation="related", weight=0.3
                        )

    async def _initialize_ml_models(self):
        """Initialize machine learning models"""
        # Student clustering model for personalization
        self.clustering_model = KMeans(n_clusters=5, random_state=42)

    async def _load_path_templates(self):
        """Load predefined path templates"""
        self.path_templates = {
            "mathematics_foundation": {
                "title": "Matematik Temelleri",
                "objectives": ["math_algebra_linear_eq", "math_geometry_triangles"],
                "type": LearningPathType.SEQUENTIAL,
            },
            "advanced_mathematics": {
                "title": "İleri Matematik",
                "objectives": ["math_algebra_quadratic_eq", "math_geometry_similarity"],
                "type": LearningPathType.ADAPTIVE,
            },
            "physics_mechanics": {
                "title": "Fizik Mekaniği",
                "objectives": [
                    "physics_mechanics_force",
                    "physics_mechanics_newton_laws",
                ],
                "type": LearningPathType.SEQUENTIAL,
            },
        }

    async def generate_personalized_path(
        self,
        student_id: str,
        learning_goals: List[str],
        context: PathOptimizationContext,
        path_type: LearningPathType = LearningPathType.ADAPTIVE,
    ) -> LearningPath:
        """Generate a personalized learning path"""

        if not self.ready:
            await self.initialize()

        logger.info(f"Generating personalized path for student {student_id}")

        # Step 1: Analyze student profile and current knowledge
        student_analysis = await self._analyze_student_profile(student_id)

        # Step 2: Determine required objectives for goals
        required_objectives = await self._identify_required_objectives(learning_goals)

        # Step 3: Filter based on current knowledge and prerequisites
        optimized_objectives = await self._optimize_objective_selection(
            required_objectives, student_analysis, context
        )

        # Step 4: Generate optimal sequence
        learning_sequence = await self._generate_optimal_sequence(
            optimized_objectives, student_analysis, context
        )

        # Step 5: Create learning nodes with resources
        learning_nodes = await self._create_learning_nodes(
            learning_sequence, student_analysis, context
        )

        # Step 6: Build final path
        learning_path = await self._build_learning_path(
            student_id, learning_nodes, learning_goals, context, path_type
        )

        # Step 7: Optimize for engagement and efficiency
        optimized_path = await self._optimize_path_for_student(
            learning_path, student_analysis, context
        )

        logger.info(f"Generated path with {len(optimized_path.nodes)} nodes")

        return optimized_path

    async def _analyze_student_profile(self, student_id: str) -> Dict[str, Any]:
        """Analyze student profile for personalization"""
        # This would typically load from database
        # For now, create a sample analysis

        analysis = {
            "current_mastery": {
                "math_algebra_linear_eq": 0.8,
                "math_geometry_triangles": 0.6,
                "physics_mechanics_force": 0.4,
            },
            "learning_style": "visual",
            "difficulty_preference": 0.6,
            "pace_preference": 0.7,
            "engagement_patterns": {
                "video": 0.8,
                "interactive": 0.9,
                "text": 0.5,
                "quiz": 0.7,
            },
            "time_patterns": {
                "optimal_session_length": 45,  # minutes
                "preferred_times": ["morning", "afternoon"],
            },
            "performance_trends": {
                "mathematics": 0.1,  # improving
                "physics": -0.05,  # slightly declining
                "chemistry": 0.0,  # stable
            },
            "struggle_areas": ["abstract_concepts", "complex_calculations"],
            "strength_areas": ["visual_problems", "step_by_step_procedures"],
        }

        return analysis

    async def _identify_required_objectives(
        self, learning_goals: List[str]
    ) -> List[str]:
        """Identify all objectives needed to achieve learning goals"""
        required_objectives = set()

        # Map goals to specific objectives (simplified)
        goal_mappings = {
            "algebra_mastery": ["math_algebra_linear_eq", "math_algebra_quadratic_eq"],
            "geometry_basics": ["math_geometry_triangles", "math_geometry_similarity"],
            "physics_mechanics": [
                "physics_mechanics_force",
                "physics_mechanics_newton_laws",
            ],
        }

        for goal in learning_goals:
            if goal in goal_mappings:
                required_objectives.update(goal_mappings[goal])

        # Add prerequisites using graph traversal
        all_objectives = set(required_objectives)
        for obj_id in required_objectives:
            if obj_id in self.objective_database:
                # Add all prerequisites
                prereqs = self._get_all_prerequisites(obj_id)
                all_objectives.update(prereqs)

        return list(all_objectives)

    def _get_all_prerequisites(self, objective_id: str) -> Set[str]:
        """Get all prerequisites for an objective (recursive)"""
        prerequisites = set()

        if objective_id in self.objective_database:
            direct_prereqs = self.objective_database[objective_id].prerequisites
            prerequisites.update(direct_prereqs)

            # Recursively get prerequisites of prerequisites
            for prereq in direct_prereqs:
                prerequisites.update(self._get_all_prerequisites(prereq))

        return prerequisites

    async def _optimize_objective_selection(
        self,
        required_objectives: List[str],
        student_analysis: Dict[str, Any],
        context: PathOptimizationContext,
    ) -> List[str]:
        """Optimize objective selection based on student needs and constraints"""

        optimized = []
        current_mastery = student_analysis.get("current_mastery", {})

        for obj_id in required_objectives:
            # Skip if already mastered
            if current_mastery.get(obj_id, 0) >= 0.9:
                continue

            # Include if in focus areas
            if context.focus_areas:
                objective = self.objective_database.get(obj_id)
                if objective and objective.topic in context.focus_areas:
                    optimized.append(obj_id)
                    continue

            # Skip if in avoid areas
            if context.avoid_areas:
                objective = self.objective_database.get(obj_id)
                if objective and objective.topic in context.avoid_areas:
                    continue

            # Include based on importance and student needs
            objective = self.objective_database.get(obj_id)
            if objective:
                current_score = current_mastery.get(obj_id, 0)
                improvement_potential = (
                    1 - current_score
                ) * objective.importance_weight

                if improvement_potential > 0.3:  # Threshold for inclusion
                    optimized.append(obj_id)

        return optimized

    async def _generate_optimal_sequence(
        self,
        objectives: List[str],
        student_analysis: Dict[str, Any],
        context: PathOptimizationContext,
    ) -> List[str]:
        """Generate optimal learning sequence using topological sort and optimization"""

        # Create subgraph with only required objectives
        subgraph = self.learning_graph.subgraph(objectives).copy()

        # Perform topological sort to respect prerequisites
        try:
            base_sequence = list(nx.topological_sort(subgraph))
        except nx.NetworkXError:
            # Handle cycles by removing some edges
            base_sequence = self._handle_dependency_cycles(subgraph)

        # Optimize sequence based on student preferences and constraints
        optimized_sequence = await self._optimize_sequence_order(
            base_sequence, student_analysis, context
        )

        return optimized_sequence

    def _handle_dependency_cycles(self, graph: nx.DiGraph) -> List[str]:
        """Handle dependency cycles in the learning graph"""
        # Find and break cycles
        cycles = list(nx.simple_cycles(graph))

        for cycle in cycles:
            # Remove the edge with lowest weight in the cycle
            min_weight = float("inf")
            edge_to_remove = None

            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                if graph.has_edge(u, v):
                    weight = graph[u][v].get("weight", 1.0)
                    if weight < min_weight:
                        min_weight = weight
                        edge_to_remove = (u, v)

            if edge_to_remove:
                graph.remove_edge(*edge_to_remove)

        return list(nx.topological_sort(graph))

    async def _optimize_sequence_order(
        self,
        base_sequence: List[str],
        student_analysis: Dict[str, Any],
        context: PathOptimizationContext,
    ) -> List[str]:
        """Optimize the order of objectives in the sequence"""

        # Group objectives that can be learned in parallel
        parallel_groups = self._identify_parallel_groups(base_sequence)

        optimized_sequence = []

        for group in parallel_groups:
            if len(group) == 1:
                optimized_sequence.extend(group)
            else:
                # Sort group based on optimization criteria
                sorted_group = await self._sort_parallel_group(
                    group, student_analysis, context
                )
                optimized_sequence.extend(sorted_group)

        return optimized_sequence

    def _identify_parallel_groups(self, sequence: List[str]) -> List[List[str]]:
        """Identify groups of objectives that can be learned in parallel"""
        groups = []
        current_group = []

        for obj_id in sequence:
            # Check if this objective depends on any in current group
            depends_on_current = any(
                self.learning_graph.has_edge(other_id, obj_id)
                for other_id in current_group
            )

            if depends_on_current:
                # Start new group
                if current_group:
                    groups.append(current_group)
                current_group = [obj_id]
            else:
                # Can be parallel with current group
                current_group.append(obj_id)

        if current_group:
            groups.append(current_group)

        return groups

    async def _sort_parallel_group(
        self,
        group: List[str],
        student_analysis: Dict[str, Any],
        context: PathOptimizationContext,
    ) -> List[str]:
        """Sort a group of parallel objectives based on optimization criteria"""

        # Calculate scores for each objective
        scores = {}
        current_mastery = student_analysis.get("current_mastery", {})

        for obj_id in group:
            objective = self.objective_database.get(obj_id)
            if not objective:
                scores[obj_id] = 0
                continue

            score = 0

            # Learning gap score (higher for bigger gaps)
            gap = 1 - current_mastery.get(obj_id, 0)
            score += gap * 0.3

            # Importance weight
            score += objective.importance_weight * 0.2

            # Difficulty appropriateness
            target_difficulty = context.difficulty_tolerance
            difficulty_match = 1 - abs(objective.difficulty_level - target_difficulty)
            score += difficulty_match * 0.2

            # Time efficiency
            time_efficiency = 1 / (
                objective.estimated_time / 60
            )  # Prefer shorter objectives
            score += time_efficiency * 0.1

            # Student strength alignment
            if objective.topic in student_analysis.get("strength_areas", []):
                score += 0.1
            elif objective.topic in student_analysis.get("struggle_areas", []):
                score -= 0.1

            scores[obj_id] = score

        # Sort by score (descending)
        sorted_group = sorted(group, key=lambda x: scores.get(x, 0), reverse=True)

        return sorted_group

    async def _create_learning_nodes(
        self,
        sequence: List[str],
        student_analysis: Dict[str, Any],
        context: PathOptimizationContext,
    ) -> List[LearningNode]:
        """Create learning nodes with resources and activities"""

        nodes = []
        cumulative_time = 0

        for i, obj_id in enumerate(sequence):
            objective = self.objective_database.get(obj_id)
            if not objective:
                continue

            # Determine node type based on position and objective
            node_type = await self._determine_node_type(objective, i, len(sequence))

            # Create base node
            node = LearningNode(
                node_id=f"node_{i+1}_{obj_id}", objective=objective, node_type=node_type
            )

            # Set scheduling
            node.scheduled_start = datetime.now() + timedelta(minutes=cumulative_time)
            node.scheduled_end = node.scheduled_start + timedelta(
                minutes=objective.estimated_time
            )
            cumulative_time += objective.estimated_time

            # Add resources based on learning style
            await self._add_personalized_resources(node, student_analysis)

            # Add activities based on objective type
            await self._add_learning_activities(node, student_analysis)

            # Add assessments
            await self._add_assessments(node, student_analysis)

            nodes.append(node)

        return nodes

    async def _determine_node_type(
        self, objective: LearningObjective, position: int, total_nodes: int
    ) -> LearningNodeType:
        """Determine the type of learning node"""

        # First nodes are typically concept introduction
        if position < total_nodes * 0.3:
            return LearningNodeType.CONCEPT

        # Middle nodes are skill practice
        elif position < total_nodes * 0.7:
            return (
                LearningNodeType.SKILL
                if position % 2 == 0
                else LearningNodeType.PRACTICE
            )

        # Later nodes are assessment and projects
        else:
            return (
                LearningNodeType.ASSESSMENT
                if position % 2 == 0
                else LearningNodeType.PROJECT
            )

    async def _add_personalized_resources(
        self, node: LearningNode, student_analysis: Dict[str, Any]
    ):
        """Add personalized learning resources to node"""

        learning_style = student_analysis.get("learning_style", "visual")
        engagement_patterns = student_analysis.get("engagement_patterns", {})

        # Resource types based on learning style
        resource_types = {
            "visual": ["video", "diagram", "infographic"],
            "auditory": ["audio", "podcast", "explanation"],
            "kinesthetic": ["interactive", "simulation", "hands_on"],
        }

        preferred_types = resource_types.get(learning_style, ["video", "text"])

        # Add resources based on preferences
        for resource_type in preferred_types:
            engagement_score = engagement_patterns.get(resource_type, 0.5)
            if engagement_score > 0.6:  # Only add if likely to engage
                resource = {
                    "type": resource_type,
                    "title": f"{node.objective.title} - {resource_type.title()}",
                    "estimated_time": node.objective.estimated_time
                    // len(preferred_types),
                    "engagement_score": engagement_score,
                    "url": f"https://example.com/resource/{node.objective.objective_id}/{resource_type}",
                }
                node.resources.append(resource)

    async def _add_learning_activities(
        self, node: LearningNode, student_analysis: Dict[str, Any]
    ):
        """Add learning activities to node"""

        # Activity types based on node type
        activity_mappings = {
            LearningNodeType.CONCEPT: ["read", "watch", "explore"],
            LearningNodeType.SKILL: ["practice", "drill", "apply"],
            LearningNodeType.PRACTICE: ["exercise", "problem_solve", "simulate"],
            LearningNodeType.ASSESSMENT: ["quiz", "test", "evaluate"],
            LearningNodeType.PROJECT: ["create", "design", "implement"],
            LearningNodeType.REFLECTION: ["reflect", "review", "synthesize"],
        }

        activity_types = activity_mappings.get(node.node_type, ["practice"])

        for activity_type in activity_types:
            activity = {
                "type": activity_type,
                "title": f"{activity_type.title()} - {node.objective.title}",
                "estimated_time": node.objective.estimated_time // len(activity_types),
                "difficulty_level": node.objective.difficulty_level,
                "instructions": f"Complete {activity_type} activities for {node.objective.title}",
            }
            node.activities.append(activity)

    async def _add_assessments(
        self, node: LearningNode, student_analysis: Dict[str, Any]
    ):
        """Add assessments to node"""

        # Assessment types based on objective
        assessment_types = node.objective.assessment_methods or ["quiz"]

        for assessment_type in assessment_types:
            assessment = {
                "type": assessment_type,
                "title": f"{node.objective.title} - {assessment_type.title()}",
                "mastery_threshold": node.objective.mastery_threshold,
                "estimated_time": 15,  # Default assessment time
                "question_count": 5 if assessment_type == "quiz" else 1,
            }
            node.assessments.append(assessment)

    async def _build_learning_path(
        self,
        student_id: str,
        nodes: List[LearningNode],
        learning_goals: List[str],
        context: PathOptimizationContext,
        path_type: LearningPathType,
    ) -> LearningPath:
        """Build the complete learning path"""

        # Calculate total estimated duration
        total_duration = sum(node.objective.estimated_time for node in nodes)

        # Build dependencies
        dependencies = {}
        for i, node in enumerate(nodes):
            deps = []
            for j in range(i):
                prev_node = nodes[j]
                if (
                    node.objective.objective_id
                    in self.objective_database.get(
                        prev_node.objective.objective_id,
                        LearningObjective("", "", "", "", ""),
                    ).enables
                ):
                    deps.append(prev_node.node_id)
            dependencies[node.node_id] = deps

        # Create learning path
        path = LearningPath(
            path_id=f"path_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            student_id=student_id,
            path_type=path_type,
            subject=nodes[0].objective.subject if nodes else "general",
            title=f"Özelleştirilmiş Öğrenme Yolu - {', '.join(learning_goals)}",
            description=f"{len(nodes)} aşamalı kişiselleştirilmiş öğrenme programı",
            learning_goals=learning_goals,
            target_completion=datetime.now() + timedelta(minutes=total_duration),
            estimated_duration=total_duration,
            nodes=nodes,
            dependencies=dependencies,
        )

        # Set learning style weights
        path.learning_style_weights = {
            "visual": 0.4,
            "auditory": 0.3,
            "kinesthetic": 0.3,
        }

        return path

    async def _optimize_path_for_student(
        self,
        path: LearningPath,
        student_analysis: Dict[str, Any],
        context: PathOptimizationContext,
    ) -> LearningPath:
        """Final optimization of the learning path"""

        # Adjust difficulty based on student preferences
        difficulty_pref = student_analysis.get("difficulty_preference", 0.5)

        for node in path.nodes:
            # Adjust difficulty
            if difficulty_pref > 0.7:  # Student prefers challenge
                node.difficulty_adjustment = min(
                    0.2, 0.8 - node.objective.difficulty_level
                )
            elif difficulty_pref < 0.3:  # Student prefers easier content
                node.difficulty_adjustment = max(
                    -0.2, 0.2 - node.objective.difficulty_level
                )

        # Optimize scheduling based on available time
        if context.available_time:
            await self._optimize_scheduling(
                path, context.available_time, context.deadline
            )

        # Update path metadata
        path.difficulty_preference = difficulty_pref
        path.pace_preference = student_analysis.get("pace_preference", 0.5)
        path.last_updated = datetime.now()

        return path

    async def _optimize_scheduling(
        self, path: LearningPath, available_time: int, deadline: Optional[datetime]
    ):
        """Optimize scheduling of learning nodes"""

        total_time_needed = sum(node.objective.estimated_time for node in path.nodes)

        if deadline:
            # Calculate if deadline is achievable
            time_until_deadline = (deadline - datetime.now()).total_seconds() / 60
            if total_time_needed > time_until_deadline:
                # Need to compress or skip some content
                await self._compress_path_for_deadline(path, time_until_deadline)

        # Schedule nodes with available time constraints
        weekly_minutes = available_time
        current_week_minutes = 0
        current_date = datetime.now()

        for node in path.nodes:
            node_time = node.objective.estimated_time

            if current_week_minutes + node_time > weekly_minutes:
                # Move to next week
                current_date += timedelta(weeks=1)
                current_week_minutes = 0

            node.scheduled_start = current_date
            node.scheduled_end = current_date + timedelta(minutes=node_time)
            current_date = node.scheduled_end
            current_week_minutes += node_time

    async def _compress_path_for_deadline(
        self, path: LearningPath, available_time: float
    ):
        """Compress learning path to fit deadline"""

        # Sort nodes by importance
        nodes_by_importance = sorted(
            path.nodes, key=lambda n: n.objective.importance_weight, reverse=True
        )

        # Keep most important nodes that fit in time
        cumulative_time = 0
        compressed_nodes = []

        for node in nodes_by_importance:
            if cumulative_time + node.objective.estimated_time <= available_time:
                compressed_nodes.append(node)
                cumulative_time += node.objective.estimated_time

        # Update path with compressed nodes
        path.nodes = compressed_nodes
        path.estimated_duration = cumulative_time

        # Rebuild dependencies for remaining nodes
        remaining_ids = {node.node_id for node in compressed_nodes}
        new_dependencies = {}

        for node_id, deps in path.dependencies.items():
            if node_id in remaining_ids:
                new_dependencies[node_id] = [d for d in deps if d in remaining_ids]

        path.dependencies = new_dependencies


# Global instance
adaptive_path_generator = AdaptiveLearningPathGenerator()


async def get_learning_path_generator() -> AdaptiveLearningPathGenerator:
    """Get initialized learning path generator"""
    if not adaptive_path_generator.ready:
        await adaptive_path_generator.initialize()
    return adaptive_path_generator
