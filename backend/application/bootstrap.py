import logging

from application.commands.auth import (
    LoginCommand,
    LoginCommandHandler,
    RefreshTokenCommand,
    RefreshTokenCommandHandler,
    RegisterUserCommand,
    RegisterUserCommandHandler,
    VeliOnayVerifyCommand,
    VeliOnayVerifyCommandHandler,
    VeliOnayWithdrawCommand,
    VeliOnayWithdrawCommandHandler,
)
from application.commands.diary import (
    AdjustGoalCommand,
    AdjustGoalCommandHandler,
    AnalyzeEntriesForInsightsCommand,
    AnalyzeEntriesForInsightsCommandHandler,
    CreateEncryptedBackupCommand,
    CreateEncryptedBackupCommandHandler,
    CreateExportCommand,
    CreateExportCommandHandler,
    CreateGoalCommand,
    CreateGoalCommandHandler,
    CreateGoalRetrospectiveCommand,
    CreateGoalRetrospectiveCommandHandler,
    CreateLearningEntryCommand,
    CreateLearningEntryCommandHandler,
    CreateReflectionCommand,
    CreateReflectionCommandHandler,
    CreateShareLinkCommand,
    CreateShareLinkCommandHandler,
    CreateSummaryCommand,
    CreateSummaryCommandHandler,
    DeleteGoalCommand,
    DeleteGoalCommandHandler,
    DeleteInsightCommand,
    DeleteInsightCommandHandler,
    DeleteSummaryCommand,
    DeleteSummaryCommandHandler,
    LinkConceptsCommand,
    LinkConceptsCommandHandler,
    RecordReviewCommand,
    RecordReviewCommandHandler,
    TrackEmotionalStateCommand,
    TrackEmotionalStateCommandHandler,
    UpdateGoalCommand,
    UpdateGoalCommandHandler,
    UpdateGoalProgressCommand,
    UpdateGoalProgressCommandHandler,
    UpdateSummaryCommand,
    UpdateSummaryCommandHandler,
)
from application.commands.learning_path import (
    AdaptLearningPathCommand,
    AdaptLearningPathCommandHandler,
    AssessKnowledgeCommand,
    AssessKnowledgeCommandHandler,
    CreateLearningPathCommand,
    CreateLearningPathCommandHandler,
    CreateStudentProfileCommand,
    CreateStudentProfileCommandHandler,
    RegisterWrongAnswersCommand,
    RegisterWrongAnswersCommandHandler,
    SearchResourcesCommand,
    SearchResourcesCommandHandler,
    SubmitQuizCommand,
    SubmitQuizCommandHandler,
    SubmitReviewCommand,
    SubmitReviewCommandHandler,
    UpdateCompletionStatusCommand,
    UpdateCompletionStatusCommandHandler,
    UpdateProgressCommand,
    UpdateProgressCommandHandler,
)
from application.commands.sinav import (
    CancelExamCommand,
    CancelExamCommandHandler,
    CompleteExamCommand,
    CompleteExamCommandHandler,
    CreateBetaPracticeCommand,
    CreateBetaPracticeCommandHandler,
    CreateExamCommand,
    CreateExamCommandHandler,
    FlagQuestionCommand,
    FlagQuestionCommandHandler,
    NavigateQuestionCommand,
    NavigateQuestionCommandHandler,
    SaveAnswerCommand,
    SaveAnswerCommandHandler,
    StartExamCommand,
    StartExamCommandHandler,
)
from core.cqrs.bus import get_command_bus

logger = logging.getLogger(__name__)


def bootstrap_cqrs():
    logger.info("Bootstrapping CQRS handlers...")
    command_bus = get_command_bus()
    # query_bus = get_query_bus()

    # Register commands
    command_bus.register(
        CreateStudentProfileCommand, CreateStudentProfileCommandHandler()
    )
    command_bus.register(AssessKnowledgeCommand, AssessKnowledgeCommandHandler())
    command_bus.register(CreateLearningPathCommand, CreateLearningPathCommandHandler())
    command_bus.register(SearchResourcesCommand, SearchResourcesCommandHandler())
    command_bus.register(AdaptLearningPathCommand, AdaptLearningPathCommandHandler())
    command_bus.register(
        UpdateCompletionStatusCommand, UpdateCompletionStatusCommandHandler()
    )
    command_bus.register(SubmitQuizCommand, SubmitQuizCommandHandler())
    command_bus.register(UpdateProgressCommand, UpdateProgressCommandHandler())
    command_bus.register(SubmitReviewCommand, SubmitReviewCommandHandler())
    command_bus.register(
        RegisterWrongAnswersCommand, RegisterWrongAnswersCommandHandler()
    )

    command_bus.register(CreateSummaryCommand, CreateSummaryCommandHandler())
    command_bus.register(UpdateSummaryCommand, UpdateSummaryCommandHandler())
    command_bus.register(DeleteSummaryCommand, DeleteSummaryCommandHandler())
    command_bus.register(CreateGoalCommand, CreateGoalCommandHandler())
    command_bus.register(UpdateGoalCommand, UpdateGoalCommandHandler())
    command_bus.register(UpdateGoalProgressCommand, UpdateGoalProgressCommandHandler())
    command_bus.register(AdjustGoalCommand, AdjustGoalCommandHandler())
    command_bus.register(
        CreateGoalRetrospectiveCommand, CreateGoalRetrospectiveCommandHandler()
    )
    command_bus.register(DeleteGoalCommand, DeleteGoalCommandHandler())
    command_bus.register(
        AnalyzeEntriesForInsightsCommand, AnalyzeEntriesForInsightsCommandHandler()
    )
    command_bus.register(DeleteInsightCommand, DeleteInsightCommandHandler())
    command_bus.register(CreateReflectionCommand, CreateReflectionCommandHandler())
    command_bus.register(
        CreateLearningEntryCommand, CreateLearningEntryCommandHandler()
    )
    command_bus.register(RecordReviewCommand, RecordReviewCommandHandler())
    command_bus.register(LinkConceptsCommand, LinkConceptsCommandHandler())
    command_bus.register(
        TrackEmotionalStateCommand, TrackEmotionalStateCommandHandler()
    )
    command_bus.register(CreateExportCommand, CreateExportCommandHandler())
    command_bus.register(CreateShareLinkCommand, CreateShareLinkCommandHandler())
    command_bus.register(
        CreateEncryptedBackupCommand, CreateEncryptedBackupCommandHandler()
    )

    command_bus.register(RegisterUserCommand, RegisterUserCommandHandler())
    command_bus.register(LoginCommand, LoginCommandHandler())
    command_bus.register(RefreshTokenCommand, RefreshTokenCommandHandler())
    command_bus.register(VeliOnayVerifyCommand, VeliOnayVerifyCommandHandler())
    command_bus.register(VeliOnayWithdrawCommand, VeliOnayWithdrawCommandHandler())

    command_bus.register(CreateExamCommand, CreateExamCommandHandler())
    command_bus.register(CreateBetaPracticeCommand, CreateBetaPracticeCommandHandler())
    command_bus.register(StartExamCommand, StartExamCommandHandler())
    command_bus.register(SaveAnswerCommand, SaveAnswerCommandHandler())
    command_bus.register(NavigateQuestionCommand, NavigateQuestionCommandHandler())
    command_bus.register(FlagQuestionCommand, FlagQuestionCommandHandler())
    command_bus.register(CompleteExamCommand, CompleteExamCommandHandler())
    command_bus.register(CancelExamCommand, CancelExamCommandHandler())

    logger.info("CQRS handlers bootstrapped successfully.")
