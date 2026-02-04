"""
LangChain-based Study Buddy Agent
Advanced educational agent using LangChain framework
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# LangChain imports
from langchain.agents import (
    AgentExecutor,
    create_structured_chat_agent,
    create_openai_functions_agent,
)
from langchain.chains import LLMChain, SequentialChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.output_parsers import (
    PydanticOutputParser,
    ResponseSchema,
    StructuredOutputParser,
)
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools import StructuredTool, tool
from pydantic import BaseModel, Field

# Import our LangChain service
from ..core.langchain_llm_service import get_langchain_service

logger = logging.getLogger(__name__)


# Pydantic models for structured outputs
class QuizQuestion(BaseModel):
    """Quiz question model"""

    question: str = Field(description="The question text")
    options: List[str] = Field(description="Multiple choice options")
    correct_answer: str = Field(description="The correct answer")
    explanation: str = Field(description="Explanation of the answer")
    difficulty: str = Field(description="Difficulty level: easy, medium, hard")


class LearningPath(BaseModel):
    """Learning path model"""

    topic: str = Field(description="Main topic")
    subtopics: List[str] = Field(description="List of subtopics to cover")
    difficulty_progression: List[str] = Field(description="Difficulty levels in order")
    estimated_time: int = Field(description="Estimated time in minutes")
    resources: List[str] = Field(description="Recommended resources")


class StudentAssessment(BaseModel):
    """Student assessment model"""

    understanding_level: float = Field(description="Understanding level 0-1")
    strengths: List[str] = Field(description="Areas of strength")
    weaknesses: List[str] = Field(description="Areas needing improvement")
    recommendations: List[str] = Field(description="Study recommendations")


class LangChainStudyBuddy:
    """LangChain-based Study Buddy Agent"""

    def __init__(self):
        self.llm_service = get_langchain_service()
        self.tools = []
        self.agent_executor = None
        self.memory = None
        self.chains = {}

        self._initialize()

    def _initialize(self):
        """Initialize LangChain components"""

        # Initialize memory
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm_service.chat_model or self.llm_service.llm,
            max_token_limit=2000,
            return_messages=True,
            memory_key="chat_history",
        )

        # Create tools
        self._create_tools()

        # Create chains
        self._create_chains()

        # Create agent
        self._create_agent()

        logger.info("LangChain Study Buddy initialized")

    def _create_tools(self):
        """Create LangChain tools for the agent"""

        # Math solver tool
        @tool
        def solve_math(expression: str) -> str:
            """Solve mathematical expressions"""
            try:
                # Remove unsafe characters
                safe_expr = expression.replace("^", "**")
                result = eval(safe_expr, {"__builtins__": {}}, {})
                return f"Result: {result}"
            except Exception as e:
                return f"Error solving: {str(e)}"

        # Quiz generator tool
        @tool
        def generate_quiz(topic: str, count: int = 5) -> str:
            """Generate quiz questions on a topic"""
            questions = []
            for i in range(count):
                questions.append(
                    {
                        "question": f"{topic} question {i+1}?",
                        "options": ["A", "B", "C", "D"],
                        "answer": "A",
                    }
                )
            return json.dumps(questions, ensure_ascii=False)

        # Explanation generator tool
        @tool
        def explain_concept(concept: str, level: str = "simple") -> str:
            """Explain a concept at different levels"""
            explanations = {
                "simple": f"{concept}: Basic explanation suitable for beginners",
                "intermediate": f"{concept}: Detailed explanation with examples",
                "advanced": f"{concept}: In-depth analysis with technical details",
            }
            return explanations.get(level, explanations["simple"])

        # Study plan creator tool
        @tool
        def create_study_plan(subject: str, duration: int = 30) -> str:
            """Create a study plan for a subject"""
            plan = {
                "subject": subject,
                "duration_minutes": duration,
                "sessions": [f"Session {i+1}: {duration//3} minutes" for i in range(3)],
                "topics": ["Introduction", "Core Concepts", "Practice"],
            }
            return json.dumps(plan, ensure_ascii=False)

        # Progress tracker tool
        @tool
        def track_progress(student_id: str, topic: str, score: float) -> str:
            """Track student progress on topics"""
            progress = {
                "student_id": student_id,
                "topic": topic,
                "score": score,
                "timestamp": datetime.now().isoformat(),
                "status": "completed" if score > 0.7 else "needs_review",
            }
            return json.dumps(progress, ensure_ascii=False)

        # Add tools to list
        self.tools = [
            solve_math,
            generate_quiz,
            explain_concept,
            create_study_plan,
            track_progress,
        ]

        # Create structured tools for specific tasks
        self.quiz_tool = StructuredTool.from_function(
            func=self._generate_structured_quiz,
            name="structured_quiz",
            description="Generate structured quiz with validation",
        )

        self.assessment_tool = StructuredTool.from_function(
            func=self._assess_student,
            name="assess_student",
            description="Assess student understanding",
        )

        self.tools.extend([self.quiz_tool, self.assessment_tool])

    def _create_chains(self):
        """Create LangChain chains for complex workflows"""

        # Quiz generation chain
        quiz_prompt = ChatPromptTemplate.from_template(
            """Generate {count} quiz questions about {topic} for grade {grade} students.
            Difficulty level: {difficulty}
            
            Format as JSON with: question, options, correct_answer, explanation
            """
        )

        self.chains["quiz_chain"] = LLMChain(
            llm=self.llm_service.chat_model or self.llm_service.llm,
            prompt=quiz_prompt,
            output_key="quiz",
        )

        # Learning path chain
        path_prompt = ChatPromptTemplate.from_template(
            """Create a personalized learning path for {student_name} to learn {topic}.
            Current level: {current_level}
            Learning style: {learning_style}
            Available time: {time_available} hours
            
            Include:
            1. Subtopics in logical order
            2. Difficulty progression
            3. Recommended resources
            4. Practice exercises
            """
        )

        self.chains["learning_path_chain"] = LLMChain(
            llm=self.llm_service.chat_model or self.llm_service.llm,
            prompt=path_prompt,
            output_key="learning_path",
        )

        # Explanation chain with examples
        explain_prompt = ChatPromptTemplate.from_template(
            """Explain {concept} to a {grade} grade student.
            Use {learning_style} learning style.
            Include:
            - Simple definition
            - Real-world example
            - Visual description if applicable
            - Practice problem
            
            Language: {language}
            """
        )

        self.chains["explanation_chain"] = LLMChain(
            llm=self.llm_service.chat_model or self.llm_service.llm,
            prompt=explain_prompt,
            output_key="explanation",
        )

        # Sequential chain for complete lesson
        self.chains["lesson_chain"] = SequentialChain(
            chains=[self.chains["explanation_chain"], self.chains["quiz_chain"]],
            input_variables=[
                "concept",
                "topic",
                "grade",
                "learning_style",
                "language",
                "count",
                "difficulty",
            ],
            output_variables=["explanation", "quiz"],
            verbose=True,
        )

        # Assessment chain with output parser
        assessment_schema = [
            ResponseSchema(
                name="understanding", description="Understanding level 0-100"
            ),
            ResponseSchema(name="strengths", description="List of strengths"),
            ResponseSchema(name="improvements", description="Areas for improvement"),
            ResponseSchema(name="next_steps", description="Recommended next steps"),
        ]

        assessment_parser = StructuredOutputParser.from_response_schemas(
            assessment_schema
        )

        assessment_prompt = ChatPromptTemplate.from_template(
            """Assess the student's understanding based on their responses:
            Questions: {questions}
            Answers: {answers}
            
            {format_instructions}
            """
        ).partial(format_instructions=assessment_parser.get_format_instructions())

        self.chains["assessment_chain"] = LLMChain(
            llm=self.llm_service.chat_model or self.llm_service.llm,
            prompt=assessment_prompt,
            output_parser=assessment_parser,
        )

    def _create_agent(self):
        """Create LangChain agent with tools"""

        # Agent prompt
        system_message = """You are an advanced AI study buddy that helps students learn effectively.
        You have access to various tools to help students:
        - Generate quizzes and practice problems
        - Explain concepts at different levels
        - Create personalized study plans
        - Track learning progress
        - Solve mathematical problems
        
        Always:
        1. Be encouraging and supportive
        2. Adapt to the student's level
        3. Provide clear explanations
        4. Use examples when helpful
        5. Check understanding with questions
        
        Respond in the student's preferred language (default: Turkish).
        """

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create agent based on available LLM
        if self.llm_service.chat_model:
            # Use OpenAI Functions Agent if available
            try:
                self.agent = OpenAIFunctionsAgent(
                    llm=self.llm_service.chat_model, tools=self.tools, prompt=prompt
                )
            except:
                # Fallback to structured chat agent
                self.agent = create_structured_chat_agent(
                    llm=self.llm_service.chat_model, tools=self.tools, prompt=prompt
                )
        else:
            # Use structured chat agent for other LLMs
            from langchain.agents import create_react_agent

            self.agent = create_react_agent(
                llm=self.llm_service.llm, tools=self.tools, prompt=prompt
            )

        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=True,
        )

    async def _generate_structured_quiz(
        self, topic: str, grade: int = 8, count: int = 5, difficulty: str = "medium"
    ) -> str:
        """Generate structured quiz using Pydantic model"""

        # Use output parser
        parser = PydanticOutputParser(pydantic_object=QuizQuestion)

        prompt = ChatPromptTemplate.from_template(
            """Generate a quiz question about {topic} for grade {grade}.
            Difficulty: {difficulty}
            
            {format_instructions}
            """
        ).partial(format_instructions=parser.get_format_instructions())

        chain = LLMChain(
            llm=self.llm_service.chat_model or self.llm_service.llm, prompt=prompt
        )

        questions = []
        for i in range(count):
            result = await chain.arun(topic=topic, grade=grade, difficulty=difficulty)

            try:
                question = parser.parse(result)
                questions.append(question.dict())
            except:
                # Fallback to simple format
                questions.append(
                    {
                        "question": f"{topic} question {i+1}",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "explanation": "Explanation here",
                        "difficulty": difficulty,
                    }
                )

        return json.dumps(questions, ensure_ascii=False)

    async def _assess_student(self, questions: List[str], answers: List[str]) -> str:
        """Assess student performance"""

        parser = PydanticOutputParser(pydantic_object=StudentAssessment)

        prompt = ChatPromptTemplate.from_template(
            """Assess student performance:
            Questions: {questions}
            Student answers: {answers}
            
            {format_instructions}
            """
        ).partial(format_instructions=parser.get_format_instructions())

        chain = LLMChain(
            llm=self.llm_service.chat_model or self.llm_service.llm, prompt=prompt
        )

        result = await chain.arun(
            questions=json.dumps(questions, ensure_ascii=False),
            answers=json.dumps(answers, ensure_ascii=False),
        )

        try:
            assessment = parser.parse(result)
            return assessment.json()
        except:
            return json.dumps(
                {
                    "understanding_level": 0.7,
                    "strengths": ["Good effort"],
                    "weaknesses": ["Needs practice"],
                    "recommendations": ["Review materials"],
                }
            )

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Main chat interface"""

        try:
            # Add context to message if provided
            if context:
                enriched_message = (
                    f"Context: {json.dumps(context)}\n\nMessage: {message}"
                )
            else:
                enriched_message = message

            # Run agent
            result = await self.agent_executor.arun(input=enriched_message)

            # Get intermediate steps for debugging
            intermediate_steps = []
            if hasattr(self.agent_executor, "return_intermediate_steps"):
                intermediate_steps = self.agent_executor.intermediate_steps

            return {
                "success": True,
                "response": result,
                "session_id": session_id,
                "memory": self.memory.chat_memory.messages[-10:],  # Last 10 messages
                "tools_used": [step[0].tool for step in intermediate_steps]
                if intermediate_steps
                else [],
            }

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
            }

    async def generate_lesson(
        self,
        topic: str,
        grade: int = 8,
        learning_style: str = "visual",
        language: str = "tr",
    ) -> Dict[str, Any]:
        """Generate complete lesson with explanation and quiz"""

        try:
            result = await self.chains["lesson_chain"].arun(
                concept=topic,
                topic=topic,
                grade=grade,
                learning_style=learning_style,
                language=language,
                count=5,
                difficulty="medium",
            )

            return {
                "success": True,
                "topic": topic,
                "explanation": result.get("explanation", ""),
                "quiz": result.get("quiz", ""),
                "metadata": {
                    "grade": grade,
                    "learning_style": learning_style,
                    "language": language,
                },
            }

        except Exception as e:
            logger.error(f"Lesson generation error: {e}")
            return {"success": False, "error": str(e)}

    async def create_learning_path(
        self,
        student_name: str,
        topic: str,
        current_level: str = "beginner",
        learning_style: str = "visual",
        time_available: int = 10,
    ) -> Dict[str, Any]:
        """Create personalized learning path"""

        try:
            result = await self.chains["learning_path_chain"].arun(
                student_name=student_name,
                topic=topic,
                current_level=current_level,
                learning_style=learning_style,
                time_available=time_available,
            )

            # Try to parse as LearningPath model
            try:
                parser = PydanticOutputParser(pydantic_object=LearningPath)
                path = parser.parse(result)
                return {"success": True, "learning_path": path.dict()}
            except:
                return {"success": True, "learning_path": result}

        except Exception as e:
            logger.error(f"Learning path creation error: {e}")
            return {"success": False, "error": str(e)}

    async def assess_understanding(
        self, questions: List[str], answers: List[str]
    ) -> Dict[str, Any]:
        """Assess student understanding based on Q&A"""

        try:
            result = self.chains["assessment_chain"].run(
                questions=questions, answers=answers
            )

            return {"success": True, "assessment": result}

        except Exception as e:
            logger.error(f"Assessment error: {e}")
            return {"success": False, "error": str(e)}

    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")

    def get_conversation_summary(self) -> str:
        """Get conversation summary"""
        if hasattr(self.memory, "moving_summary_buffer"):
            return self.memory.moving_summary_buffer

        messages = self.memory.chat_memory.messages
        if not messages:
            return "No conversation history"

        summary = []
        for msg in messages[-5:]:
            if isinstance(msg, HumanMessage):
                summary.append(f"Student: {msg.content[:100]}")
            elif isinstance(msg, AIMessage):
                summary.append(f"Tutor: {msg.content[:100]}")

        return "\n".join(summary)


# Example usage
async def example_usage():
    """Example of using LangChain Study Buddy"""

    buddy = LangChainStudyBuddy()

    # Simple chat
    response = await buddy.chat("Matematik öğrenmek istiyorum")
    print(f"Response: {response['response']}")

    # Generate lesson
    lesson = await buddy.generate_lesson(
        topic="Kesirler", grade=6, learning_style="visual", language="tr"
    )
    print(f"Lesson: {lesson}")

    # Create learning path
    path = await buddy.create_learning_path(
        student_name="Ahmet",
        topic="Geometri",
        current_level="beginner",
        learning_style="kinesthetic",
        time_available=5,
    )
    print(f"Learning Path: {path}")

    # Assess understanding
    assessment = await buddy.assess_understanding(
        questions=["What is 2+2?", "What is 3*3?"], answers=["4", "9"]
    )
    print(f"Assessment: {assessment}")


if __name__ == "__main__":
    asyncio.run(example_usage())
