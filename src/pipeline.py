# Orchestration logic (run_automated_pipeline)

from src.knowledge import StructuredProjectContext, CorporateTaxonomyNormalizer
from src.rag import SimpleVectorStore
from src.rules import GapDetector
from src.llm import synthesize_report_with_llm
from src.report import generate_formatted_report
from src.config import DATABASE_FILE_DESTINATION


def run_automated_pipeline() -> str:
    # 1. Initialize
    normalizer = CorporateTaxonomyNormalizer()
    context = StructuredProjectContext(normalizer=normalizer)
    store = SimpleVectorStore()

    # 2. Data Ingestion & Indexing
    context.ingest_data()
    if DATABASE_FILE_DESTINATION.exists():
        store.load(DATABASE_FILE_DESTINATION)
    else:
        store.build_indices(context.raw_chunks)
        store.save(DATABASE_FILE_DESTINATION)

    # 3. Audit
    detector = GapDetector(context, store, normalizer)
    internal_findings = detector.execute_audit_checks()
    heatmap = detector.generate_strategic_heatmap()

    # 4. Synthesis & Reporting
    raw_payload = {
        "findings": [f.model_dump() for f in internal_findings],
        "strategic_heatmap": heatmap
    }
    structured_report = synthesize_report_with_llm(raw_payload)

    return generate_formatted_report(structured_report)