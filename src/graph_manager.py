import json
import os
from typing import List, Dict, Optional

class GraphManager:
    def __init__(self, graph_path="knowledge_graph/graph.json"):
        self.graph_path = graph_path
        self.data = {"nodes": {}, "edges": []}

    def add_node(self, node_id, node_type, **kwargs):
        self.data["nodes"][node_id] = {"id": node_id, "type": node_type, **kwargs}

    def add_edge(self, from_id, to_id, edge_type):
        self.data["edges"].append({"from": from_id, "to": to_id, "type": edge_type})

    def save(self):
        directory = os.path.dirname(self.graph_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(self.graph_path, "w") as f:
            # Flatten nodes for JSON
            output = {
                "nodes": list(self.data["nodes"].values()),
                "edges": self.data["edges"]
            }
            json.dump(output, f, indent=2)

    def load(self):
        with open(self.graph_path, "r") as f:
            raw = json.load(f)
            self.data = {
                "nodes": {n["id"]: n for n in raw["nodes"]},
                "edges": raw["edges"]
            }

    def get_related(self, from_id, edge_type=None) -> List[Dict]:
        """Find nodes related to from_id."""
        related_ids = [
            e["to"] for e in self.data["edges"] 
            if e["from"] == from_id and (edge_type is None or e["type"] == edge_type)
        ]
        return [self.data["nodes"][rid] for rid in related_ids if rid in self.data["nodes"]]
