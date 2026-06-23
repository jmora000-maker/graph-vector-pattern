# Orchestration logic (run_automated_pipeline)
from src.knowledge import StructuredProjectContext, CorporateTaxonomyNormalizer
from src.rules import AuditDetector


def run_automated_pipeline():
    """
    Orchestrates the end-to-end data ingestion, structuring, and audit process.
    """
    # 1. Initialize the normalization utility
    normalizer = CorporateTaxonomyNormalizer()

    # 2. Initialize the project context (data layer)
    # Note: Pydantic models initialize empty lists by default
    context = StructuredProjectContext()

    # 3. Ingest raw data from your inputs layer
    context.ingest_data()

    # 4. Run automated audit checks
    detector = AuditDetector(context, normalizer)
    internal_findings = detector.execute_audit_checks()

    # 5. Return the findings for UI rendering
    return internal_findings