import networkx as nx
import requests
import json
import re
from typing import List, Tuple, Dict

class GraphManager:
    def __init__(self, ollama_url: str = "http://localhost:11434/api/generate", model: str = "phi4-mini:latest"):
        self.graph = nx.Graph()
        self.ollama_url = ollama_url
        self.model = model

    def set_model(self, model: str):
        """Update the model used for triple extraction."""
        self.model = model

    def _ask_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=120
            )
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""

    def extract_triples(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Extracts (subject, relation, object) triples from text using LLM.
        """
        prompt = f"""Extract key entities and their relationships from the following text. 
Format the output as a JSON list of triples: [["entity1", "relationship", "entity2"], ...].
If no relationships are found, return an empty list [].
Only return the JSON list, no other text.

Text:
{text}
"""
        response = self._ask_ollama(prompt)
        try:
            # Clean response to ensure it's valid JSON
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return []
        except Exception as e:
            print(f"Error parsing triples: {e}")
            return []

    def add_text_to_graph(self, text: str):
        """
        Processes text, extracts triples, and adds them to the NetworkX graph.
        """
        triples = self.extract_triples(text)
        if not isinstance(triples, list):
            return

        for triple in triples:
            if isinstance(triple, list) and len(triple) >= 3:
                subj, rel, obj = triple[0], triple[1], triple[2]
                self.graph.add_edge(subj, obj, relation=rel)
            else:
                print(f"Skipping invalid triple: {triple}")

    def get_related_context(self, entity: str, depth: int = 1) -> str:
        """
        Finds related entities and their relations to expand context.
        """
        if entity not in self.graph:
            return ""
        
        related_info = []
        # Find neighbors within specified depth
        nodes = nx.single_source_shortest_path_length(self.graph, entity, cutoff=depth)
        
        for node in nodes:
            for neighbor in self.graph.neighbors(node):
                rel = self.graph[node][neighbor].get('relation', 'related to')
                related_info.append(f"{node} --({rel})--> {neighbor}")
        
        return "\n".join(related_info)

    def save_graph(self, path: str):
        """
        Saves the graph to a JSON file.
        """
        try:
            data = nx.node_link_data(self.graph)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving graph to JSON: {e}")

    def load_graph(self, path: str):
        """
        Loads the graph from a JSON file.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
        except FileNotFoundError:
            self.graph = nx.Graph()
        except Exception as e:
            print(f"Error loading graph from JSON: {e}")
            self.graph = nx.Graph()
