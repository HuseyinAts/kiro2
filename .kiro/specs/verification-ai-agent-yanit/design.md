# Design Document - AI Agent Yanıt Doğrulama Sistemi

## Overview

AI Agent Yanıt Doğrulama Sistemi, Boris Cherny'nin verification feedback loops prensibine göre tasarlanmış, AI agent'ların (LearningPathAgent, StudyBuddyAgent, ExamAgent) ürettiği yanıtların doğruluğunu ve tutarlılığını garanti eden otomatik doğrulama sistemidir. Sistem, her AI yanıtını 3 katmanlı doğrulama ile kontrol eder ve 0-1 arası confidence score üretir.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              AI Agent (LearningPath/StudyBuddy/Exam)         │
│                    Yanıt Üretimi Tamamlandı                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Stop Hook Trigger                         │
│              (AI yanıt tamamlandığında)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Response Validation Orchestrator                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Layer 1: Agent-Specific Validation  (30% weight)    │  │
│  │  Layer 2: Fact-Checking System       (40% weight)    │  │
│  │  Layer 3: Consistency Checker        (30% weight)    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Confidence Score Calculator                     │
│            (Weighted Average: 0.0 - 1.0)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                  Score >= 0.8?
                         │
            ┌────────────┴────────────┐
            │                         │
         YES│                         │NO
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │Yanıt Onaylandı│         │Score >= 0.5? │
    │   (Approve)  │          │              │
    └──────────────┘          └──────┬───────┘
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                     YES│                         │NO
                        ▼                         ▼
                ┌──────────────┐          ┌──────────────┐
                │Manuel İnceleme│         │Yanıt Reddedildi│
                │   (Review)   │          │   (Reject)   │
                └──────────────┘          └──────────────┘
```

### Component Architecture

```python
# Core Components
app/
├── validators/
│   ├── __init__.py
│   ├── base_response_validator.py      # Abstract base class
│   ├── learning_path_validator.py      # LearningPathAgent validator
│   ├── study_buddy_validator.py        # StudyBuddyAgent validator
│   └── exam_agent_validator.py         # ExamAgent validator
├── fact_checking/
│   ├── __init__.py
│   ├── fact_checker.py                 # Main fact-checking engine
│   ├── rag_client.py                   # RAG system integration
│   ├── wikipedia_client.py             # Wikipedia API client
│   └── meb_resource_client.py          # MEB resource checker
├── consistency/
│   ├── __init__.py
│   ├── consistency_checker.py          # Response consistency analyzer
│   └── response_history_manager.py     # Manage response history
├── scoring/
│   ├── __init__.py
│   └── confidence_scorer.py            # Confidence score calculator
├── hooks/
│   ├── __init__.py
│   └── stop_hook.py                    # Stop Hook implementation
└── orchestrator/
    ├── __init__.py
    └── response_validation_orchestrator.py  # Main coordinator
```


## Components and Interfaces

### 1. Base Response Validator (Abstract)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class ValidationResult(BaseModel):
    """Validation result model"""
    is_valid: bool
    score: float  # 0-1
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metadata: Dict[str, any]

class AgentResponse(BaseModel):
    """AI Agent response model"""
    agent_type: str  # "learning_path", "study_buddy", "exam"
    response_id: str
    user_id: str
    query: str
    response_text: str
    response_data: Dict  # Agent-specific structured data
    timestamp: datetime
    context: Optional[Dict] = None

class BaseResponseValidator(ABC):
    """Abstract base validator for AI responses"""
    
    def __init__(self, weight: float):
        self.weight = weight
    
    @abstractmethod
    async def validate(self, response: AgentResponse) -> ValidationResult:
        """Validate AI response and return result"""
        pass
    
    @abstractmethod
    def get_validator_name(self) -> str:
        """Return validator name"""
        pass
```

### 2. LearningPath Validator

```python
class LearningPathValidator(BaseResponseValidator):
    """Validates LearningPathAgent responses"""
    
    def __init__(self, weight: float, meb_api_client):
        super().__init__(weight)
        self.meb_api = meb_api_client
    
    async def validate(self, response: AgentResponse) -> ValidationResult:
        errors = []
        warnings = []
        score = 1.0
        
        learning_path = response.response_data.get("learning_path", {})
        
        # 1. Müfredat uyumu kontrolü
        topics = learning_path.get("topics", [])
        grade_level = response.context.get("grade_level")
        
        for topic in topics:
            is_valid = await self.meb_api.validate_topic(topic, grade_level)
            if not is_valid:
                errors.append(f"Konu müfredatta yok: {topic}")
                score -= 0.2
        
        # 2. Ön koşul ilişkileri kontrolü
        prerequisites = learning_path.get("prerequisites", {})
        for topic, prereqs in prerequisites.items():
            if not self._validate_prerequisite_order(topic, prereqs, topics):
                errors.append(f"Ön koşul sıralaması hatalı: {topic}")
                score -= 0.15
        
        # 3. Zorluk seviyesi kontrolü
        student_level = response.context.get("student_level", "orta")
        difficulty = learning_path.get("difficulty")
        
        if not self._is_appropriate_difficulty(difficulty, student_level):
            warnings.append("Zorluk seviyesi öğrenci seviyesine uygun değil")
            score -= 0.1
        
        # 4. Tahmini süre kontrolü
        estimated_hours = learning_path.get("estimated_hours", 0)
        topic_count = len(topics)
        
        if estimated_hours < topic_count * 2:  # Min 2 saat per topic
            warnings.append("Tahmini süre çok kısa görünüyor")
            score -= 0.05
        
        if estimated_hours > topic_count * 10:  # Max 10 saat per topic
            warnings.append("Tahmini süre çok uzun görünüyor")
            score -= 0.05
        
        # 5. Kaynak erişilebilirliği kontrolü
        resources = learning_path.get("resources", [])
        for resource in resources:
            is_accessible = await self._check_resource_accessibility(resource)
            if not is_accessible:
                warnings.append(f"Kaynak erişilebilir değil: {resource['title']}")
                score -= 0.05
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_suggestions(errors, warnings),
            metadata={"validator": "LearningPath", "topic_count": len(topics)}
        )
    
    def _validate_prerequisite_order(self, topic: str, prereqs: List[str], 
                                     all_topics: List[str]) -> bool:
        """Check if prerequisites come before the topic in learning path"""
        topic_index = all_topics.index(topic) if topic in all_topics else -1
        
        for prereq in prereqs:
            prereq_index = all_topics.index(prereq) if prereq in all_topics else -1
            if prereq_index >= topic_index:
                return False
        
        return True
    
    async def _check_resource_accessibility(self, resource: Dict) -> bool:
        """Check if resource URL is accessible"""
        url = resource.get("url")
        if not url:
            return True  # No URL to check
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=5) as resp:
                    return resp.status == 200
        except:
            return False
```


### 3. StudyBuddy Validator

```python
class StudyBuddyValidator(BaseResponseValidator):
    """Validates StudyBuddyAgent responses"""
    
    def __init__(self, weight: float):
        super().__init__(weight)
    
    async def validate(self, response: AgentResponse) -> ValidationResult:
        errors = []
        warnings = []
        score = 1.0
        
        query = response.query
        answer = response.response_text
        
        # 1. Konu ilgisi kontrolü
        relevance_score = await self._calculate_relevance(query, answer)
        if relevance_score < 0.7:
            errors.append("Cevap soruyla ilgili değil")
            score -= 0.3
        elif relevance_score < 0.85:
            warnings.append("Cevap kısmen ilgili")
            score -= 0.1
        
        # 2. Matematiksel doğruluk kontrolü (eğer matematik sorusuysa)
        if self._is_math_question(query):
            math_correct = await self._verify_math_answer(query, answer)
            if not math_correct:
                errors.append("Matematiksel hesaplama hatalı")
                score -= 0.4
        
        # 3. Tarihsel doğruluk kontrolü (eğer tarih sorusuysa)
        if self._is_history_question(query):
            historical_facts = self._extract_historical_facts(answer)
            for fact in historical_facts:
                is_correct = await self._verify_historical_fact(fact)
                if not is_correct:
                    errors.append(f"Tarihsel bilgi hatalı: {fact}")
                    score -= 0.3
        
        # 4. Bilimsel doğruluk kontrolü (eğer fen sorusuysa)
        if self._is_science_question(query):
            scientific_claims = self._extract_scientific_claims(answer)
            for claim in scientific_claims:
                is_valid = await self._verify_scientific_claim(claim)
                if not is_valid:
                    errors.append(f"Bilimsel açıklama hatalı: {claim}")
                    score -= 0.3
        
        # 5. Kaynak güvenilirliği kontrolü
        sources = response.response_data.get("sources", [])
        for source in sources:
            is_reliable = self._check_source_reliability(source)
            if not is_reliable:
                warnings.append(f"Kaynak güvenilir değil: {source}")
                score -= 0.1
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_suggestions(errors, warnings),
            metadata={"validator": "StudyBuddy", "relevance_score": relevance_score}
        )
    
    async def _calculate_relevance(self, query: str, answer: str) -> float:
        """Calculate semantic relevance between query and answer"""
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        query_embedding = model.encode(query)
        answer_embedding = model.encode(answer)
        
        # Cosine similarity
        similarity = np.dot(query_embedding, answer_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(answer_embedding)
        )
        
        return float(similarity)
    
    async def _verify_math_answer(self, query: str, answer: str) -> bool:
        """Verify mathematical correctness using SymPy"""
        from sympy import sympify, simplify
        
        try:
            # Extract mathematical expressions from query and answer
            query_expr = self._extract_math_expression(query)
            answer_expr = self._extract_math_expression(answer)
            
            if not query_expr or not answer_expr:
                return True  # Cannot verify, assume correct
            
            # Parse and simplify
            query_sympy = sympify(query_expr)
            answer_sympy = sympify(answer_expr)
            
            # Check if they're equivalent
            return simplify(query_sympy - answer_sympy) == 0
        except:
            return True  # Cannot verify, assume correct
```


### 4. ExamAgent Validator

```python
class ExamAgentValidator(BaseResponseValidator):
    """Validates ExamAgent responses"""
    
    def __init__(self, weight: float):
        super().__init__(weight)
    
    async def validate(self, response: AgentResponse) -> ValidationResult:
        errors = []
        warnings = []
        score = 1.0
        
        evaluation = response.response_data.get("evaluation", {})
        
        # 1. Puanlama tutarlılığı kontrolü
        scoring_consistent = self._check_scoring_consistency(evaluation)
        if not scoring_consistent:
            errors.append("Puanlama kriterleri tutarsız uygulanmış")
            score -= 0.3
        
        # 2. Matematiksel hesaplama kontrolü
        correct_count = evaluation.get("correct_count", 0)
        wrong_count = evaluation.get("wrong_count", 0)
        total_questions = evaluation.get("total_questions", 0)
        
        if correct_count + wrong_count != total_questions:
            errors.append("Doğru/yanlış sayısı toplam soru sayısına eşit değil")
            score -= 0.4
        
        # 3. İstatistiksel hesaplama kontrolü
        statistics = evaluation.get("statistics", {})
        
        # Verify average calculation
        scores = evaluation.get("question_scores", [])
        if scores:
            calculated_avg = sum(scores) / len(scores)
            reported_avg = statistics.get("average_score", 0)
            
            if abs(calculated_avg - reported_avg) > 0.01:
                errors.append("Ortalama hesaplaması hatalı")
                score -= 0.2
        
        # 4. Zayıf alan tespiti doğruluğu
        weak_areas = evaluation.get("weak_areas", [])
        question_results = evaluation.get("question_results", [])
        
        for area in weak_areas:
            area_questions = [q for q in question_results if q["topic"] == area]
            if not area_questions:
                warnings.append(f"Zayıf alan tespiti veriye dayanmıyor: {area}")
                score -= 0.1
            else:
                # Check if area is actually weak (< 60% correct)
                correct_ratio = sum(1 for q in area_questions if q["is_correct"]) / len(area_questions)
                if correct_ratio >= 0.6:
                    warnings.append(f"Alan zayıf değil ama zayıf olarak işaretlenmiş: {area}")
                    score -= 0.1
        
        # 5. Öneri uygunluğu kontrolü
        recommendations = evaluation.get("recommendations", [])
        student_profile = response.context.get("student_profile", {})
        
        for rec in recommendations:
            is_appropriate = self._check_recommendation_appropriateness(
                rec, student_profile, weak_areas
            )
            if not is_appropriate:
                warnings.append(f"Öneri öğrenci profiline uygun değil: {rec}")
                score -= 0.05
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_suggestions(errors, warnings),
            metadata={"validator": "ExamAgent", "total_questions": total_questions}
        )
    
    def _check_scoring_consistency(self, evaluation: Dict) -> bool:
        """Check if scoring criteria are consistently applied"""
        question_results = evaluation.get("question_results", [])
        
        # Group by difficulty level
        by_difficulty = {}
        for result in question_results:
            difficulty = result.get("difficulty", "orta")
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = []
            by_difficulty[difficulty].append(result)
        
        # Check if similar questions get similar scores
        for difficulty, results in by_difficulty.items():
            if len(results) < 2:
                continue
            
            scores = [r["score"] for r in results if r.get("is_correct")]
            if scores:
                # Standard deviation should be low for consistent scoring
                std_dev = np.std(scores)
                if std_dev > 10:  # High variance
                    return False
        
        return True
```


### 5. Fact-Checking System

```python
class FactChecker:
    """Main fact-checking engine using RAG and external sources"""
    
    def __init__(self, rag_client, wikipedia_client, meb_client):
        self.rag = rag_client
        self.wikipedia = wikipedia_client
        self.meb = meb_client
    
    async def check_facts(self, response: AgentResponse) -> ValidationResult:
        """Check factual accuracy of AI response"""
        errors = []
        warnings = []
        score = 1.0
        
        # Extract factual claims from response
        claims = self._extract_claims(response.response_text)
        
        verified_claims = []
        
        for claim in claims:
            # 1. Check against RAG system (internal knowledge base)
            rag_result = await self.rag.verify_claim(claim)
            
            # 2. Check against Wikipedia (external validation)
            wiki_result = await self.wikipedia.verify_claim(claim)
            
            # 3. Check against MEB resources (authoritative source)
            meb_result = await self.meb.verify_claim(claim)
            
            # Combine results with priority: MEB > RAG > Wikipedia
            verification = self._combine_verifications(
                claim, rag_result, wiki_result, meb_result
            )
            
            verified_claims.append(verification)
            
            if verification["status"] == "false":
                errors.append(f"Yanlış bilgi: {claim}")
                score -= 0.3
            elif verification["status"] == "unverified":
                warnings.append(f"Doğrulanamayan bilgi: {claim}")
                score -= 0.1
            elif verification["status"] == "partially_true":
                warnings.append(f"Kısmen doğru bilgi: {claim}")
                score -= 0.05
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_fact_corrections(verified_claims),
            metadata={
                "fact_checker": "RAG+Wikipedia+MEB",
                "claims_checked": len(claims),
                "verified_claims": verified_claims
            }
        )
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text using NLP"""
        # Use spaCy or similar to extract factual statements
        # For now, simple sentence splitting
        sentences = text.split('.')
        
        # Filter out questions and opinions
        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Skip questions
            if '?' in sentence:
                continue
            
            # Skip opinion markers
            opinion_markers = ['sanırım', 'bence', 'galiba', 'belki']
            if any(marker in sentence.lower() for marker in opinion_markers):
                continue
            
            claims.append(sentence)
        
        return claims
    
    def _combine_verifications(self, claim: str, rag_result: Dict, 
                               wiki_result: Dict, meb_result: Dict) -> Dict:
        """Combine verification results with priority weighting"""
        
        # Priority: MEB (60%) > RAG (30%) > Wikipedia (10%)
        if meb_result["found"]:
            confidence = meb_result["confidence"] * 0.6
            status = meb_result["status"]
            source = "MEB"
        elif rag_result["found"]:
            confidence = rag_result["confidence"] * 0.3
            status = rag_result["status"]
            source = "RAG"
        elif wiki_result["found"]:
            confidence = wiki_result["confidence"] * 0.1
            status = wiki_result["status"]
            source = "Wikipedia"
        else:
            confidence = 0.0
            status = "unverified"
            source = "none"
        
        return {
            "claim": claim,
            "status": status,  # "true", "false", "partially_true", "unverified"
            "confidence": confidence,
            "source": source,
            "evidence": meb_result.get("evidence") or rag_result.get("evidence") or wiki_result.get("evidence")
        }

class RAGClient:
    """RAG system client for internal knowledge base"""
    
    async def verify_claim(self, claim: str) -> Dict:
        """Verify claim against RAG knowledge base"""
        # Query vector database
        results = await self._query_vector_db(claim)
        
        if not results:
            return {"found": False, "confidence": 0.0, "status": "unverified"}
        
        # Calculate semantic similarity
        best_match = results[0]
        similarity = best_match["score"]
        
        if similarity > 0.9:
            status = "true"
            confidence = similarity
        elif similarity > 0.7:
            status = "partially_true"
            confidence = similarity * 0.8
        else:
            status = "unverified"
            confidence = 0.0
        
        return {
            "found": True,
            "confidence": confidence,
            "status": status,
            "evidence": best_match["text"]
        }

class WikipediaClient:
    """Wikipedia API client for fact verification"""
    
    async def verify_claim(self, claim: str) -> Dict:
        """Verify claim against Turkish Wikipedia"""
        import aiohttp
        
        # Search Wikipedia
        search_url = "https://tr.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": claim,
            "format": "json",
            "utf8": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=params) as resp:
                data = await resp.json()
        
        results = data.get("query", {}).get("search", [])
        
        if not results:
            return {"found": False, "confidence": 0.0, "status": "unverified"}
        
        # Get first result content
        page_title = results[0]["title"]
        content = await self._get_page_content(page_title)
        
        # Check if claim is mentioned in content
        claim_lower = claim.lower()
        content_lower = content.lower()
        
        if claim_lower in content_lower:
            status = "true"
            confidence = 0.8
        else:
            # Calculate semantic similarity
            similarity = self._calculate_similarity(claim, content)
            if similarity > 0.7:
                status = "partially_true"
                confidence = similarity * 0.7
            else:
                status = "unverified"
                confidence = 0.0
        
        return {
            "found": True,
            "confidence": confidence,
            "status": status,
            "evidence": content[:500]  # First 500 chars
        }
```


### 6. Consistency Checker

```python
class ConsistencyChecker:
    """Checks consistency with previous AI responses"""
    
    def __init__(self, response_history_manager):
        self.history = response_history_manager
    
    async def check_consistency(self, response: AgentResponse) -> ValidationResult:
        """Check if response is consistent with previous responses"""
        errors = []
        warnings = []
        score = 1.0
        
        # Get last 10 responses from same agent for same user
        previous_responses = await self.history.get_recent_responses(
            user_id=response.user_id,
            agent_type=response.agent_type,
            limit=10
        )
        
        if not previous_responses:
            # No history to compare, assume consistent
            return ValidationResult(
                is_valid=True,
                score=1.0,
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={"consistency_checker": "no_history"}
            )
        
        # Extract topics from current response
        current_topics = self._extract_topics(response.response_text)
        
        contradictions = []
        
        for prev_response in previous_responses:
            # Check for contradictions on same topics
            prev_topics = self._extract_topics(prev_response.response_text)
            
            common_topics = set(current_topics.keys()) & set(prev_topics.keys())
            
            for topic in common_topics:
                current_statement = current_topics[topic]
                prev_statement = prev_topics[topic]
                
                # Check if statements contradict
                is_contradiction = await self._detect_contradiction(
                    current_statement, prev_statement
                )
                
                if is_contradiction:
                    contradictions.append({
                        "topic": topic,
                        "current": current_statement,
                        "previous": prev_statement,
                        "previous_response_id": prev_response.response_id,
                        "type": "direct"
                    })
                    score -= 0.2
        
        # Check for indirect contradictions (semantic)
        semantic_contradictions = await self._detect_semantic_contradictions(
            response, previous_responses
        )
        
        contradictions.extend(semantic_contradictions)
        score -= len(semantic_contradictions) * 0.1
        
        # Generate errors and warnings
        if contradictions:
            for contradiction in contradictions:
                if contradiction["type"] == "direct":
                    errors.append(
                        f"Çelişki tespit edildi - Konu: {contradiction['topic']}"
                    )
                else:
                    warnings.append(
                        f"Dolaylı çelişki olabilir - Konu: {contradiction['topic']}"
                    )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_consistency_suggestions(contradictions),
            metadata={
                "consistency_checker": "history_based",
                "responses_checked": len(previous_responses),
                "contradictions_found": len(contradictions)
            }
        )
    
    def _extract_topics(self, text: str) -> Dict[str, str]:
        """Extract topic-statement pairs from text"""
        # Simple implementation - can be enhanced with NLP
        topics = {}
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Try to identify topic (first noun phrase)
            words = sentence.split()
            if len(words) > 2:
                topic = words[0]  # Simplified
                topics[topic] = sentence
        
        return topics
    
    async def _detect_contradiction(self, statement1: str, statement2: str) -> bool:
        """Detect if two statements contradict each other"""
        from sentence_transformers import SentenceTransformer
        
        # Check for negation patterns
        negation_words = ['değil', 'yok', 'hayır', 'asla', 'hiç']
        
        has_negation_1 = any(word in statement1.lower() for word in negation_words)
        has_negation_2 = any(word in statement2.lower() for word in negation_words)
        
        # If one has negation and other doesn't, might be contradiction
        if has_negation_1 != has_negation_2:
            # Check semantic similarity
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            emb1 = model.encode(statement1)
            emb2 = model.encode(statement2)
            
            similarity = np.dot(emb1, emb2) / (
                np.linalg.norm(emb1) * np.linalg.norm(emb2)
            )
            
            # High similarity + opposite negation = contradiction
            if similarity > 0.7:
                return True
        
        return False
    
    async def _detect_semantic_contradictions(
        self, current: AgentResponse, previous: List[AgentResponse]
    ) -> List[Dict]:
        """Detect semantic contradictions using embeddings"""
        contradictions = []
        
        # This is a placeholder for more sophisticated semantic analysis
        # Could use LLM to detect contradictions
        
        return contradictions

class ResponseHistoryManager:
    """Manages AI response history in Redis"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def save_response(self, response: AgentResponse):
        """Save response to history"""
        key = f"response_history:{response.user_id}:{response.agent_type}"
        
        # Store as JSON
        response_json = response.json()
        
        # Add to list (keep last 50)
        await self.redis.lpush(key, response_json)
        await self.redis.ltrim(key, 0, 49)
        
        # Set expiry (30 days)
        await self.redis.expire(key, 30 * 24 * 60 * 60)
    
    async def get_recent_responses(
        self, user_id: str, agent_type: str, limit: int = 10
    ) -> List[AgentResponse]:
        """Get recent responses from history"""
        key = f"response_history:{user_id}:{agent_type}"
        
        # Get from Redis
        responses_json = await self.redis.lrange(key, 0, limit - 1)
        
        # Parse JSON
        responses = []
        for resp_json in responses_json:
            try:
                response = AgentResponse.parse_raw(resp_json)
                responses.append(response)
            except:
                continue
        
        return responses
```


### 7. Confidence Score Calculator

```python
class ConfidenceScorer:
    """Calculates weighted confidence score from all validators"""
    
    WEIGHTS = {
        "agent_specific": 0.30,
        "fact_checking": 0.40,
        "consistency": 0.30
    }
    
    def calculate_confidence(
        self,
        agent_validation: ValidationResult,
        fact_checking: ValidationResult,
        consistency: ValidationResult
    ) -> float:
        """Calculate weighted confidence score (0-1)"""
        
        total_score = (
            agent_validation.score * self.WEIGHTS["agent_specific"] +
            fact_checking.score * self.WEIGHTS["fact_checking"] +
            consistency.score * self.WEIGHTS["consistency"]
        )
        
        return round(total_score, 3)
    
    def determine_action(self, confidence: float) -> str:
        """Determine action based on confidence score"""
        if confidence >= 0.8:
            return "approve"
        elif confidence >= 0.5:
            return "review"
        else:
            return "reject"
```

### 8. Stop Hook Implementation

```python
class StopHook:
    """Hook triggered when AI agent completes response"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    async def on_response_complete(self, response: AgentResponse):
        """Triggered when AI agent completes response"""
        
        try:
            # Run validation
            validation_result = await self.orchestrator.validate_response(response)
            
            # Log results
            await self._log_validation(response, validation_result)
            
            # Take action based on confidence
            action = validation_result["action"]
            
            if action == "reject":
                # Block response and notify admin
                await self._block_response(response, validation_result)
                await self._notify_admin(response, validation_result)
            elif action == "review":
                # Flag for manual review
                await self._flag_for_review(response, validation_result)
            else:
                # Approve response
                await self._approve_response(response, validation_result)
            
        except Exception as e:
            # Log error but don't block response
            logger.error(f"Validation error: {e}")
            await self._approve_response(response, {"confidence": 0.5, "error": str(e)})
```

### 9. Response Validation Orchestrator

```python
class ResponseValidationOrchestrator:
    """Main coordinator for response validation"""
    
    def __init__(
        self,
        learning_path_validator: LearningPathValidator,
        study_buddy_validator: StudyBuddyValidator,
        exam_agent_validator: ExamAgentValidator,
        fact_checker: FactChecker,
        consistency_checker: ConsistencyChecker,
        confidence_scorer: ConfidenceScorer
    ):
        self.validators = {
            "learning_path": learning_path_validator,
            "study_buddy": study_buddy_validator,
            "exam": exam_agent_validator
        }
        self.fact_checker = fact_checker
        self.consistency_checker = consistency_checker
        self.scorer = confidence_scorer
    
    async def validate_response(self, response: AgentResponse) -> Dict:
        """Run all validations and calculate confidence score"""
        
        start_time = time.time()
        
        # 1. Agent-specific validation (30%)
        agent_validator = self.validators.get(response.agent_type)
        if not agent_validator:
            raise ValueError(f"Unknown agent type: {response.agent_type}")
        
        agent_result = await agent_validator.validate(response)
        
        # 2. Fact-checking (40%)
        fact_result = await self.fact_checker.check_facts(response)
        
        # 3. Consistency check (30%)
        consistency_result = await self.consistency_checker.check_consistency(response)
        
        # Calculate confidence score
        confidence = self.scorer.calculate_confidence(
            agent_result, fact_result, consistency_result
        )
        
        # Determine action
        action = self.scorer.determine_action(confidence)
        
        # Aggregate all errors and warnings
        all_errors = (
            agent_result.errors +
            fact_result.errors +
            consistency_result.errors
        )
        
        all_warnings = (
            agent_result.warnings +
            fact_result.warnings +
            consistency_result.warnings
        )
        
        all_suggestions = (
            agent_result.suggestions +
            fact_result.suggestions +
            consistency_result.suggestions
        )
        
        duration = time.time() - start_time
        
        return {
            "response_id": response.response_id,
            "confidence_score": confidence,
            "action": action,  # "approve", "review", "reject"
            "validation_results": {
                "agent_specific": agent_result.dict(),
                "fact_checking": fact_result.dict(),
                "consistency": consistency_result.dict()
            },
            "errors": all_errors,
            "warnings": all_warnings,
            "suggestions": all_suggestions,
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime

class AgentResponse(BaseModel):
    """AI Agent response model"""
    agent_type: Literal["learning_path", "study_buddy", "exam"]
    response_id: str
    user_id: str
    query: str
    response_text: str
    response_data: Dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Optional[Dict] = None

class ValidationResult(BaseModel):
    """Validation result model"""
    is_valid: bool
    score: float = Field(..., ge=0, le=1)
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metadata: Dict[str, any]

class ValidationReport(BaseModel):
    """Complete validation report"""
    response_id: str
    confidence_score: float = Field(..., ge=0, le=1)
    action: Literal["approve", "review", "reject"]
    validation_results: Dict
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    duration_seconds: float
    timestamp: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Confidence Score Bounds
*For any* response validation, the confidence score must be between 0 and 1 inclusive.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

### Property 2: Weighted Average Correctness
*For any* set of validator scores, the confidence score must equal the weighted average (30% agent + 40% fact + 30% consistency).
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 3: Action Threshold Consistency
*For any* response with confidence >= 0.8, the action must be "approve".
*For any* response with confidence < 0.5, the action must be "reject".
**Validates: Requirements 6.4, 7.6**

### Property 4: Validation Completeness
*For any* response validation, all three validators (agent-specific, fact-checking, consistency) must be executed.
**Validates: Requirements 6.2, 6.3**

### Property 5: Error Reporting Completeness
*For any* validation with score < 0.8, at least one error or warning must be present.
**Validates: Requirements 8.1, 8.2**

### Property 6: Performance Bound
*For any* single response validation, the total execution time must be less than 2 seconds.
**Validates: Success Metrics**

### Property 7: Fact-Checking Priority
*For any* fact-checking result, if MEB source is available, it must be prioritized over RAG and Wikipedia.
**Validates: Requirements 4.4, 4.5**

### Property 8: Consistency History Limit
*For any* consistency check, at most 10 previous responses must be analyzed.
**Validates: Requirements 5.1**

## Error Handling

- **ValidationError**: Raised when validation logic fails
- **TimeoutError**: Raised when validation exceeds 2 seconds
- **ExternalAPIError**: Raised when Wikipedia/MEB API is unavailable
- **AgentTypeError**: Raised when unknown agent type is provided
- **HistoryNotFoundError**: Raised when response history cannot be retrieved

## Testing Strategy

### Unit Tests
- Test each validator independently with mock responses
- Test confidence score calculation with various weight combinations
- Test fact-checking with mock RAG/Wikipedia/MEB clients
- Test consistency checking with mock response history

### Property Tests (Hypothesis)
- **Property 1 Test**: Generate random validator scores, verify confidence in [0, 1]
- **Property 2 Test**: Generate random scores, verify weighted average formula
- **Property 3 Test**: Generate responses with various confidence scores, verify action mapping
- **Property 6 Test**: Measure validation time for 100 random responses
- **Property 7 Test**: Generate fact-checking scenarios, verify MEB priority
- **Property 8 Test**: Generate response histories, verify max 10 checked

### Integration Tests
- Test full validation pipeline with real AI responses
- Test Stop Hook trigger mechanism
- Test database persistence of validation results
- Test Redis caching of response history

**Test Configuration**: Minimum 100 iterations per property test

## Performance Optimization

### Caching Strategy
- Cache MEB kazanım data (TTL: 1 day)
- Cache Wikipedia page content (TTL: 1 hour)
- Cache RAG query results (TTL: 30 minutes)
- Cache validation results for identical responses (TTL: 5 minutes)

### Parallel Processing
- Run all three validators in parallel using `asyncio.gather`
- Run fact-checking sources (RAG, Wikipedia, MEB) in parallel
- Limit concurrent validations to 20 per worker

### Redis Keys
- `response_history:{user_id}:{agent_type}` - Response history list
- `validation_result:{response_id}` - Cached validation result
- `fact_cache:{claim_hash}` - Cached fact-checking result
- `meb_kazanim:{topic}:{grade}` - Cached MEB kazanım data

## Monitoring and Alerting

### Metrics to Track
- Average confidence score per agent type
- Validation duration (P50, P95, P99)
- Approval/Review/Reject rates
- Error rate per validator
- Fact-checking source usage (RAG vs Wikipedia vs MEB)
- Consistency check contradiction rate

### Alerts
- Alert when average confidence < 0.7 for 1 hour
- Alert when validation duration > 2s for 10 consecutive requests
- Alert when error rate > 10% for 15 minutes
- Alert when rejection rate > 20% for 1 hour

## API Endpoints

```python
# POST /api/v1/validate-response
# Validate a single AI response
{
  "agent_type": "study_buddy",
  "response_id": "resp_123",
  "user_id": "user_456",
  "query": "Osmanlı İmparatorluğu ne zaman kuruldu?",
  "response_text": "Osmanlı İmparatorluğu 1299 yılında kuruldu.",
  "response_data": {},
  "context": {"grade_level": 10}
}

# GET /api/v1/validation-report/{response_id}
# Get validation report for a response

# GET /api/v1/validation-stats
# Get validation statistics (admin only)
```
