"""SQLAlchemy models."""

from app.models.user import User
from app.models.project import (
    ProjectMember,
    ResearchProject,
    ResearchProjectProfile,
    StageProgress,
)
from app.models.research import (
    AnalysisMapping,
    AnalysisPlan,
    Construct,
    Hypothesis,
    Instrument,
    InstrumentItem,
    InstrumentSection,
    OperationalDefinition,
    Population,
    ResearchDesign,
    ResearchGap,
    ResearchObjective,
    ResearchProblem,
    ResearchQuestion,
    SamplingPlan,
    Variable,
)
from app.models.conversation import Conversation, Message
from app.models.document import DocumentChunk, UploadedDocument
from app.models.literature import LiteratureSearch, Reference, ReferenceClaim
from app.models.manuscript import AlignmentIssue, ManuscriptSection
from app.models.decisions import AISuggestion, AuditLog, ExportRecord, ResearcherDecision
from app.models.library import (
    ComparisonItem,
    DocumentProcessingJob,
    DocumentSection,
    DocumentStageMapping,
    ExtractedResearchElement,
    LearningNote,
    PaperComparison,
    SourceAnnotation,
    SourceDocument,
)

__all__ = [
    "User",
    "ResearchProject",
    "ResearchProjectProfile",
    "ProjectMember",
    "StageProgress",
    "Conversation",
    "Message",
    "ResearchProblem",
    "ResearchGap",
    "ResearchObjective",
    "ResearchQuestion",
    "Hypothesis",
    "Construct",
    "Variable",
    "OperationalDefinition",
    "ResearchDesign",
    "Population",
    "SamplingPlan",
    "Instrument",
    "InstrumentSection",
    "InstrumentItem",
    "AnalysisPlan",
    "AnalysisMapping",
    "UploadedDocument",
    "DocumentChunk",
    "LiteratureSearch",
    "Reference",
    "ReferenceClaim",
    "ManuscriptSection",
    "AlignmentIssue",
    "ResearcherDecision",
    "AISuggestion",
    "ExportRecord",
    "AuditLog",
    "SourceDocument",
    "DocumentSection",
    "DocumentStageMapping",
    "ExtractedResearchElement",
    "DocumentProcessingJob",
    "PaperComparison",
    "ComparisonItem",
    "LearningNote",
    "SourceAnnotation",
]

from app.models.paper_review import PaperReview

from app.models.research_desk import ResearchPassage, ResearchEvidence, ResearchBrief, ResearchJob, ResearchDraft, ResearchReferenceCheck, ResearchSourceReference

from app.models.ai_configuration import AIConfiguration
