from app.domain.support_agent import ProblemReportDraft, RuleAnswer


def rule_answer_response(answer: RuleAnswer) -> dict:
    return {
        "status": answer.status,
        "answer": answer.answer,
        "citations": [
            {
                "ruleId": citation.rule_id,
                "title": citation.title,
                "sourceSection": citation.source_section,
                "sourceVersion": citation.source_version,
            }
            for citation in answer.citations
        ],
    }


def report_draft_response(draft: ProblemReportDraft) -> dict:
    return {
        "reportId": draft.report_id,
        "category": draft.category,
        "summary": draft.summary,
        "reproductionSteps": list(draft.reproduction_steps),
        "expectedBehavior": draft.expected_behavior,
        "actualBehavior": draft.actual_behavior,
        "requiresHumanConfirmation": draft.requires_human_confirmation,
        "submissionStatus": draft.submission_status,
    }
