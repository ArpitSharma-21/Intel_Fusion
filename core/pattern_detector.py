"""
Pattern detection module for anomaly and trend analysis.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import statistics

from core.graph_builder import IntelGraph
from core.timeline_builder import Timeline, TimelineBuilder
from core.nlp_pipeline import ExtractionResult
from config import analysis_config


@dataclass
class Pattern:
    """Represents a detected pattern."""
    pattern_type: str
    description: str
    entities_involved: List[str]
    significance: float  # 0-1 score
    evidence: List[str]
    recommendation: str = ""


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    anomaly_type: str
    description: str
    entity: str
    expected_value: float
    actual_value: float
    deviation: float
    severity: str  # "low", "medium", "high"


@dataclass
class PatternReport:
    """Complete pattern analysis report."""
    patterns: List[Pattern]
    anomalies: List[Anomaly]
    entity_frequency: Dict[str, int]
    relationship_frequency: Dict[str, int]
    temporal_patterns: List[Dict]
    summary: str


class PatternDetector:
    """
    Detects patterns, anomalies, and trends in extracted intelligence.
    """
    
    def __init__(self):
        self.frequency_threshold = analysis_config.frequency_threshold
        self.anomaly_threshold = analysis_config.anomaly_std_threshold
    
    def analyze(
        self,
        graph: IntelGraph,
        timeline: Timeline,
        extractions: List[ExtractionResult]
    ) -> PatternReport:
        """
        Perform comprehensive pattern analysis.
        
        Args:
            graph: The entity relationship graph
            timeline: The event timeline
            extractions: Raw extraction results
            
        Returns:
            PatternReport with all findings
        """
        patterns = []
        anomalies = []
        
        # Analyze entity frequency
        entity_freq = self._analyze_entity_frequency(extractions)
        freq_patterns = self._detect_frequency_patterns(entity_freq)
        patterns.extend(freq_patterns)
        
        # Analyze relationship frequency
        rel_freq = self._analyze_relationship_frequency(graph)
        rel_patterns = self._detect_relationship_patterns(graph, rel_freq)
        patterns.extend(rel_patterns)
        
        # Detect anomalies in frequency
        freq_anomalies = self._detect_frequency_anomalies(entity_freq)
        anomalies.extend(freq_anomalies)
        
        # Detect network-based patterns
        network_patterns = self._detect_network_patterns(graph)
        patterns.extend(network_patterns)
        
        # Detect temporal patterns
        temporal_patterns = self._detect_temporal_patterns(timeline)
        for tp in temporal_patterns:
            patterns.append(Pattern(
                pattern_type="temporal_cluster",
                description=f"Activity cluster: {tp['event_count']} events between "
                           f"{tp['start'].strftime('%Y-%m-%d')} and {tp['end'].strftime('%Y-%m-%d')}",
                entities_involved=tp['entities'][:5],
                significance=min(tp['event_count'] / 10, 1.0),
                evidence=[],
                recommendation="Review clustered events for coordinated activity"
            ))
        
        # Generate summary
        summary = self._generate_summary(patterns, anomalies, entity_freq)
        
        return PatternReport(
            patterns=sorted(patterns, key=lambda p: p.significance, reverse=True),
            anomalies=anomalies,
            entity_frequency=entity_freq,
            relationship_frequency=rel_freq,
            temporal_patterns=temporal_patterns,
            summary=summary
        )
    
    def _analyze_entity_frequency(
        self, 
        extractions: List[ExtractionResult]
    ) -> Dict[str, int]:
        """Count entity occurrences across all extractions."""
        freq = Counter()
        
        for extraction in extractions:
            for entity in extraction.entities:
                freq[entity.normalized_text] += 1
        
        return dict(freq)
    
    def _analyze_relationship_frequency(
        self, 
        graph: IntelGraph
    ) -> Dict[str, int]:
        """Analyze relationship patterns in the graph."""
        freq = {}
        
        for u, v, data in graph.graph.edges(data=True):
            key = f"{u} — {v}"
            freq[key] = data.get("weight", 1)
        
        return freq
    
    def _detect_frequency_patterns(
        self, 
        entity_freq: Dict[str, int]
    ) -> List[Pattern]:
        """Detect patterns in entity frequency."""
        patterns = []
        
        if not entity_freq:
            return patterns
        
        # Find highly frequent entities
        sorted_entities = sorted(
            entity_freq.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Top entities pattern
        top_entities = sorted_entities[:5]
        if top_entities:
            patterns.append(Pattern(
                pattern_type="high_frequency",
                description=f"Most mentioned entities in documents",
                entities_involved=[e[0] for e in top_entities],
                significance=0.7,
                evidence=[f"{e[0]}: {e[1]} mentions" for e in top_entities],
                recommendation="Focus analysis on these key entities"
            ))
        
        # Repeated mentions pattern (above threshold)
        repeated = [
            (name, count) for name, count in entity_freq.items()
            if count >= self.frequency_threshold
        ]
        
        if len(repeated) > 3:
            patterns.append(Pattern(
                pattern_type="repeated_mentions",
                description=f"{len(repeated)} entities appear {self.frequency_threshold}+ times",
                entities_involved=[r[0] for r in repeated[:10]],
                significance=0.6,
                evidence=[f"{r[0]}: {r[1]} times" for r in repeated[:5]],
                recommendation="These entities may be central to the intelligence"
            ))
        
        return patterns
    
    def _detect_relationship_patterns(
        self, 
        graph: IntelGraph,
        rel_freq: Dict[str, int]
    ) -> List[Pattern]:
        """Detect patterns in relationships."""
        patterns = []
        
        if not rel_freq:
            return patterns
        
        # Strong relationships
        strong_rels = [
            (rel, weight) for rel, weight in rel_freq.items()
            if weight >= 3
        ]
        
        if strong_rels:
            patterns.append(Pattern(
                pattern_type="strong_relationships",
                description="Entities frequently appearing together",
                entities_involved=[],
                significance=0.8,
                evidence=[f"{rel}: {w} co-occurrences" for rel, w in strong_rels[:5]],
                recommendation="Investigate nature of these relationships"
            ))
        
        return patterns
    
    def _detect_frequency_anomalies(
        self, 
        entity_freq: Dict[str, int]
    ) -> List[Anomaly]:
        """Detect statistical anomalies in entity frequency."""
        anomalies = []
        
        if len(entity_freq) < 3:
            return anomalies
        
        counts = list(entity_freq.values())
        mean = statistics.mean(counts)
        
        try:
            std = statistics.stdev(counts)
        except statistics.StatisticsError:
            return anomalies
        
        if std == 0:
            return anomalies
        
        # Find entities with unusual frequency
        for entity, count in entity_freq.items():
            z_score = (count - mean) / std
            
            if abs(z_score) > self.anomaly_threshold:
                severity = "high" if abs(z_score) > 3 else "medium"
                
                anomalies.append(Anomaly(
                    anomaly_type="frequency_anomaly",
                    description=f"'{entity}' appears unusually {'often' if z_score > 0 else 'rarely'}",
                    entity=entity,
                    expected_value=mean,
                    actual_value=count,
                    deviation=z_score,
                    severity=severity
                ))
        
        return anomalies
    
    def _detect_network_patterns(self, graph: IntelGraph) -> List[Pattern]:
        """Detect patterns in the network structure."""
        import networkx as nx
        patterns = []
        
        if len(graph.graph) < 3:
            return patterns
        
        # Hub detection (high degree centrality)
        centrality = nx.degree_centrality(graph.graph)
        hubs = [
            (node, score) for node, score in centrality.items()
            if score > 0.3  # More than 30% of possible connections
        ]
        
        if hubs:
            patterns.append(Pattern(
                pattern_type="network_hub",
                description="Central entities connecting multiple other entities",
                entities_involved=[h[0] for h in hubs],
                significance=0.85,
                evidence=[f"{h[0]}: {h[1]:.2f} centrality" for h in hubs],
                recommendation="These entities may be key connectors or coordinators"
            ))
        
        # Bridge detection (high betweenness)
        if len(graph.graph) >= 4:
            try:
                betweenness = nx.betweenness_centrality(graph.graph)
                bridges = [
                    (node, score) for node, score in betweenness.items()
                    if score > 0.2
                ]
                
                if bridges:
                    patterns.append(Pattern(
                        pattern_type="network_bridge",
                        description="Entities bridging different groups",
                        entities_involved=[b[0] for b in bridges],
                        significance=0.75,
                        evidence=[f"{b[0]}: {b[1]:.2f} betweenness" for b in bridges],
                        recommendation="These entities connect otherwise separate groups"
                    ))
            except Exception:
                pass
        
        # Cluster detection
        if len(graph.graph) >= 5:
            try:
                communities = list(nx.community.greedy_modularity_communities(graph.graph))
                if len(communities) > 1:
                    patterns.append(Pattern(
                        pattern_type="community_structure",
                        description=f"Network divides into {len(communities)} distinct groups",
                        entities_involved=[],
                        significance=0.7,
                        evidence=[
                            f"Group {i+1}: {', '.join(list(c)[:3])}..." 
                            for i, c in enumerate(communities[:3])
                        ],
                        recommendation="Analyze each group separately for targeted insights"
                    ))
            except Exception:
                pass
        
        return patterns
    
    def _detect_temporal_patterns(self, timeline: Timeline) -> List[Dict]:
        """Detect temporal patterns using timeline builder."""
        builder = TimelineBuilder()
        builder._timeline_cache = timeline
        builder.events = []  # We use the cached timeline
        
        return builder.detect_temporal_clusters(window_days=7)
    
    def _generate_summary(
        self, 
        patterns: List[Pattern],
        anomalies: List[Anomaly],
        entity_freq: Dict[str, int]
    ) -> str:
        """Generate a text summary of findings."""
        parts = []
        
        # Count summary
        parts.append(f"Analyzed {len(entity_freq)} unique entities.")
        
        # Pattern summary
        if patterns:
            high_sig = [p for p in patterns if p.significance >= 0.7]
            parts.append(f"Detected {len(patterns)} patterns ({len(high_sig)} high significance).")
        
        # Anomaly summary
        if anomalies:
            high_sev = [a for a in anomalies if a.severity == "high"]
            parts.append(f"Found {len(anomalies)} anomalies ({len(high_sev)} high severity).")
        
        # Top entity
        if entity_freq:
            top_entity = max(entity_freq.items(), key=lambda x: x[1])
            parts.append(f"Most mentioned: '{top_entity[0]}' ({top_entity[1]} times).")
        
        return " ".join(parts)
