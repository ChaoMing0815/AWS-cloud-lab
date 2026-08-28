from app.adapters.memory_support_report_repository import MemorySupportReportRepository
from app.adapters.mock_support_model import MockSupportModel
from app.adapters.static_rules_knowledge_base import StaticRulesKnowledgeBase
from app.application.support_agent import SupportAgent


def create_support_agent(repository) -> SupportAgent:
    return SupportAgent(
        model=MockSupportModel(),
        rules_knowledge_base=StaticRulesKnowledgeBase.from_default_resource(),
        report_repository=repository,
    )


def create_memory_agent() -> SupportAgent:
    return create_support_agent(MemorySupportReportRepository())
