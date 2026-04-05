"""
question_bank_v2_routes.py: scripts/ importlarini lazy try/except ile sar.
"""

path = r"C:\Users\husey\kiro2\backend\api\question_bank_v2_routes.py"

with open(path, encoding="utf-8") as f:
    content = f.read()

OLD = '''sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.ai_question_generator import HybridQuestionGenerator
from scripts.question_validator import QuestionValidator
from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
from services.plagiarism_detection_service import PlagiarismDetectionService
from services.adaptive_testing_service import ComputerAdaptiveTestingService
from services.hitl_workflow_service import (
    HITLWorkflowService,
    ReviewDecision,
    ReviewSubmission,
)'''

NEW = '''sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from scripts.ai_question_generator import HybridQuestionGenerator
    from scripts.question_validator import QuestionValidator
    _SCRIPTS_AVAILABLE = True
except ImportError:
    HybridQuestionGenerator = None
    QuestionValidator = None
    _SCRIPTS_AVAILABLE = False

try:
    from services.knowledge_graph_service import KnowledgeGraphService, QuestionNode
    from services.plagiarism_detection_service import PlagiarismDetectionService
    from services.adaptive_testing_service import ComputerAdaptiveTestingService
    from services.hitl_workflow_service import (
        HITLWorkflowService,
        ReviewDecision,
        ReviewSubmission,
    )
    _SERVICES_AVAILABLE = True
except ImportError:
    KnowledgeGraphService = None
    QuestionNode = None
    PlagiarismDetectionService = None
    ComputerAdaptiveTestingService = None
    HITLWorkflowService = None
    ReviewDecision = None
    ReviewSubmission = None
    _SERVICES_AVAILABLE = False'''

if OLD not in content:
    print("HATA: Hedef blok bulunamadi")
    idx = content.find("from scripts.ai_question_generator")
    print(f"  idx={idx}, context: {repr(content[max(0,idx-50):idx+100])}")
else:
    new_content = content.replace(OLD, NEW, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("OK: scripts/ importlari try/except ile sarildi")
    print(f"  Eski: {content.count(chr(10))+1} satir, Yeni: {new_content.count(chr(10))+1} satir")
