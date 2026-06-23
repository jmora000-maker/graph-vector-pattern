from src.pipeline import run_automated_pipeline
import os

print("Running pipeline...")
try:
    report = run_automated_pipeline()
    print("Pipeline completed successfully.")
    print("Checking if knowledge_graph/graph.json exists...")
    if os.path.exists("knowledge_graph/graph.json"):
        print("knowledge_graph/graph.json created successfully.")
    else:
        print("knowledge_graph/graph.json NOT found.")
except Exception as e:
    print(f"Pipeline failed: {e}")
