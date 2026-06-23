from src.config import database_file_destination
from src.rag import SimpleVectorStore
from src.inputs import StructuredProjectContext
from src.rules import GapDetector
from src.taxonomy import CorporateTaxonomyNormalizer
from src.llm import compile_raw_payload, synthesize_report_with_llm
from src.report import generate_executive_summary

# --- ORCHESTRATION LAYER ---
def run_automated_pipeline() -> str:
    print("PIPELINE STARTED")

    print("STEP 1: Normalizing Stakeholders and Concerns.")
    normalizer = CorporateTaxonomyNormalizer()

    print("STEP 2: Ingesting Raw Data.")
    context = StructuredProjectContext(normalizer=normalizer)
    context.ingest_data()

    print("STEP 3: Building Vector Index.")
    store = SimpleVectorStore()

    target_dir = database_file_destination.parent
    if not target_dir.exists():
        print(f" -> Creating missing directory: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)

    # 2. Build vector indices with new data
    store.build_indices(context.raw_chunks)
    store.save(database_file_destination)

    print("STEP 4: Executing Gap Detection.")
    detector = GapDetector(context, store, normalizer)

    internal_findings = detector.execute_audit_checks()

    heatmap = detector.generate_strategic_heatmap()

    print("STEP 5: Compiling Raw Payload.")
    print(f" -> Found {len(internal_findings)} internal findings.")

    # STEP 5: Compiling Raw Payload (Pass the heatmap)
    raw_payload = compile_raw_payload(internal_findings, store, heatmap)

    print("STEP 6: Synthesizing AI Report Narrative.")
    structured_report = synthesize_report_with_llm(raw_payload)

    print("STEP 7: Generating Executive Summary.")
    # Assign the returned text directly
    final_report_text = generate_executive_summary(structured_report)

    print("PIPELINE COMPLETED")
    return final_report_text



