"""
Graph construction module for entity relationship networks.
"""
import networkx as nx
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from core.nlp_pipeline import Entity, Relationship, ExtractionResult
from config import nlp_config


@dataclass
class GraphMetrics:
    """Metrics about the constructed graph."""
    node_count: int
    edge_count: int
    density: float
    components: int
    most_central: List[tuple]  # (node, centrality_score)
    most_connected: List[tuple]  # (node, degree)


class IntelGraph:
    """
    Intelligence graph representing entities and their relationships.
    
    Wraps networkx graph with intelligence-specific operations.
    """
    
    def __init__(self):
        self.graph = nx.Graph()
        self._entity_types: Dict[str, str] = {}
        self._entity_counts: Dict[str, int] = {}
    
    def add_entity(self, entity: Entity):
        """Add an entity as a node."""
        name = entity.normalized_text
        
        if name in self.graph:
            # Update count
            self.graph.nodes[name]["count"] += 1
            self.graph.nodes[name]["sentences"].append(entity.sentence)
        else:
            self.graph.add_node(
                name,
                label=entity.label,
                color=nlp_config.entity_colors.get(entity.label, "#888888"),
                count=1,
                sentences=[entity.sentence],
                document_id=entity.document_id
            )
            self._entity_types[name] = entity.label
    
    def add_relationship(self, rel: Relationship):
        """Add a relationship as an edge."""
        # Ensure both nodes exist
        if rel.source not in self.graph:
            self.graph.add_node(
                rel.source,
                label=rel.source_type,
                color=nlp_config.entity_colors.get(rel.source_type, "#888888"),
                count=1,
                sentences=[],
                document_id=""
            )
        
        if rel.target not in self.graph:
            self.graph.add_node(
                rel.target,
                label=rel.target_type,
                color=nlp_config.entity_colors.get(rel.target_type, "#888888"),
                count=1,
                sentences=[],
                document_id=""
            )
        
        if self.graph.has_edge(rel.source, rel.target):
            # Update existing edge
            self.graph[rel.source][rel.target]["weight"] += rel.weight
            self.graph[rel.source][rel.target]["contexts"].extend(rel.context)
        else:
            self.graph.add_edge(
                rel.source,
                rel.target,
                weight=rel.weight,
                relationship_type=rel.relationship_type,
                contexts=rel.context
            )
    
    def build_from_extraction(self, result: ExtractionResult):
        """Build graph from extraction results."""
        # Add all entities
        for entity in result.entities:
            self.add_entity(entity)
        
        # Add all relationships
        for rel in result.relationships:
            self.add_relationship(rel)
        
        return self
    
    def merge(self, other: 'IntelGraph'):
        """Merge another graph into this one."""
        # Merge nodes
        for node, data in other.graph.nodes(data=True):
            if node in self.graph:
                self.graph.nodes[node]["count"] += data.get("count", 1)
                self.graph.nodes[node]["sentences"].extend(data.get("sentences", []))
            else:
                self.graph.add_node(node, **data)
        
        # Merge edges
        for u, v, data in other.graph.edges(data=True):
            if self.graph.has_edge(u, v):
                self.graph[u][v]["weight"] += data.get("weight", 1)
                self.graph[u][v]["contexts"].extend(data.get("contexts", []))
            else:
                self.graph.add_edge(u, v, **data)
        
        return self
    
    def get_metrics(self) -> GraphMetrics:
        """Calculate graph metrics."""
        if len(self.graph) == 0:
            return GraphMetrics(
                node_count=0,
                edge_count=0,
                density=0,
                components=0,
                most_central=[],
                most_connected=[]
            )
        
        # Calculate centrality
        centrality = nx.degree_centrality(self.graph)
        sorted_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate degree
        degrees = dict(self.graph.degree())
        sorted_degree = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        
        return GraphMetrics(
            node_count=len(self.graph.nodes()),
            edge_count=len(self.graph.edges()),
            density=nx.density(self.graph),
            components=nx.number_connected_components(self.graph),
            most_central=sorted_central[:10],
            most_connected=sorted_degree[:10]
        )
    
    def get_subgraph(self, center_node: str, depth: int = 1) -> 'IntelGraph':
        """Get subgraph around a specific node."""
        if center_node not in self.graph:
            return IntelGraph()
        
        # BFS to find nodes within depth
        nodes = {center_node}
        frontier = {center_node}
        
        for _ in range(depth):
            new_frontier = set()
            for node in frontier:
                new_frontier.update(self.graph.neighbors(node))
            nodes.update(new_frontier)
            frontier = new_frontier
        
        # Create subgraph
        subgraph = IntelGraph()
        subgraph.graph = self.graph.subgraph(nodes).copy()
        return subgraph
    
    def get_nodes_by_type(self, entity_type: str) -> List[str]:
        """Get all nodes of a specific type."""
        return [
            node for node, data in self.graph.nodes(data=True)
            if data.get("label") == entity_type
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary format for serialization."""
        return {
            "nodes": [
                {"id": node, **data}
                for node, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **data}
                for u, v, data in self.graph.edges(data=True)
            ]
        }


class GraphBuilder:
    """Builds and manages intelligence graphs."""
    
    def __init__(self):
        self.master_graph = IntelGraph()
    
    def process_extraction(self, result: ExtractionResult) -> IntelGraph:
        """Process extraction result into a graph."""
        doc_graph = IntelGraph()
        doc_graph.build_from_extraction(result)
        
        # Merge into master graph
        self.master_graph.merge(doc_graph)
        
        return doc_graph
    
    def get_master_graph(self) -> IntelGraph:
        """Get the accumulated master graph."""
        return self.master_graph
    
    def reset(self):
        """Reset the master graph."""
        self.master_graph = IntelGraph()
