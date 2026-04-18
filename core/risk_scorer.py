"""
Risk scoring module for intelligence assessment.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

from core.graph_builder import IntelGraph, GraphMetrics
from core.pattern_detector import PatternReport
from core.timeline_builder import Timeline
from config import analysis_config


class RiskLevel(Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFactor:
    """Individual risk factor."""
    name: str
    description: str
    score: float  # 0-100
    weight: float
    evidence: List[str]


@dataclass
class RiskAssessment:
    """Complete risk assessment."""
    overall_score: float  # 0-100
    risk_level: RiskLevel
    factors: List[RiskFactor]
    key_findings: List[str]
    recommendations: List[str]


class RiskScorer:
    """
    Calculates risk scores based on extracted intelligence.
    
    Combines multiple factors into an overall risk assessment.
    """
    
    def __init__(self):
        self.weights = analysis_config.risk_weights
    
    def assess(
        self,
        graph: IntelGraph,
        timeline: Timeline,
        patterns: PatternReport
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment.
        
        Args:
            graph: Entity relationship graph
            timeline: Event timeline
            patterns: Pattern analysis report
            
        Returns:
            RiskAssessment with scores and recommendations
        """
        factors = []
        
        # Factor 1: Entity Density
        density_factor = self._assess_entity_density(graph)
        factors.append(density_factor)
        
        # Factor 2: Unusual Patterns
        pattern_factor = self._assess_patterns(patterns)
        factors.append(pattern_factor)
        
        # Factor 3: Temporal Clustering
        temporal_factor = self._assess_temporal_clustering(timeline, patterns)
        factors.append(temporal_factor)
        
        # Factor 4: Network Centrality
        network_factor = self._assess_network_centrality(graph)
        factors.append(network_factor)
        
        # Calculate overall score
        overall_score = sum(f.score * f.weight for f in factors)
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        # Generate findings and recommendations
        key_findings = self._generate_findings(factors, patterns)
        recommendations = self._generate_recommendations(factors, risk_level)
        
        return RiskAssessment(
            overall_score=round(overall_score, 1),
            risk_level=risk_level,
            factors=factors,
            key_findings=key_findings,
            recommendations=recommendations
        )
    
    def _assess_entity_density(self, graph: IntelGraph) -> RiskFactor:
        """Assess risk based on entity density and volume."""
        metrics = graph.get_metrics()
        
        # Score based on density and connectivity
        if metrics.node_count == 0:
            score = 0
        else:
            # More connected = potentially more concerning
            density_score = min(metrics.density * 100, 50)
            volume_score = min(metrics.node_count / 2, 50)
            score = density_score + volume_score
        
        evidence = []
        if metrics.node_count > 0:
            evidence.append(f"{metrics.node_count} entities identified")
            evidence.append(f"{metrics.edge_count} relationships detected")
            evidence.append(f"Network density: {metrics.density:.3f}")
        
        return RiskFactor(
            name="Entity Density",
            description="Assessment of entity volume and interconnection density",
            score=min(score, 100),
            weight=self.weights.get("entity_density", 0.2),
            evidence=evidence
        )
    
    def _assess_patterns(self, patterns: PatternReport) -> RiskFactor:
        """Assess risk based on detected patterns and anomalies."""
        score = 0
        evidence = []
        
        # High significance patterns increase risk
        high_sig_patterns = [p for p in patterns.patterns if p.significance >= 0.7]
        score += len(high_sig_patterns) * 15
        
        if high_sig_patterns:
            evidence.append(f"{len(high_sig_patterns)} high-significance patterns")
        
        # Anomalies increase risk
        high_sev_anomalies = [a for a in patterns.anomalies if a.severity == "high"]
        score += len(high_sev_anomalies) * 20
        
        if high_sev_anomalies:
            evidence.append(f"{len(high_sev_anomalies)} high-severity anomalies")
        
        # Hub patterns are concerning
        hub_patterns = [p for p in patterns.patterns if p.pattern_type == "network_hub"]
        score += len(hub_patterns) * 10
        
        if hub_patterns:
            evidence.append("Central hub entities detected")
        
        return RiskFactor(
            name="Unusual Patterns",
            description="Assessment of anomalies and suspicious patterns",
            score=min(score, 100),
            weight=self.weights.get("unusual_patterns", 0.3),
            evidence=evidence
        )
    
    def _assess_temporal_clustering(
        self, 
        timeline: Timeline,
        patterns: PatternReport
    ) -> RiskFactor:
        """Assess risk based on temporal event clustering."""
        score = 0
        evidence = []
        
        # Clustered events suggest coordinated activity
        clusters = patterns.temporal_patterns
        
        if clusters:
            score += len(clusters) * 15
            evidence.append(f"{len(clusters)} temporal clusters detected")
            
            # Large clusters are more concerning
            large_clusters = [c for c in clusters if c["event_count"] >= 5]
            score += len(large_clusters) * 10
            
            if large_clusters:
                evidence.append(f"{len(large_clusters)} large activity clusters")
        
        # Short date range with many events
        if timeline.entries and timeline.date_range[0] and timeline.date_range[1]:
            days_span = (timeline.date_range[1] - timeline.date_range[0]).days
            if days_span > 0:
                events_per_day = timeline.total_events / max(days_span, 1)
                if events_per_day > 1:
                    score += 20
                    evidence.append(f"High activity: {events_per_day:.1f} events/day")
        
        return RiskFactor(
            name="Temporal Clustering",
            description="Assessment of event timing and coordination",
            score=min(score, 100),
            weight=self.weights.get("temporal_clustering", 0.2),
            evidence=evidence
        )
    
    def _assess_network_centrality(self, graph: IntelGraph) -> RiskFactor:
        """Assess risk based on network structure."""
        import networkx as nx
        
        score = 0
        evidence = []
        
        if len(graph.graph) < 2:
            return RiskFactor(
                name="Network Centrality",
                description="Assessment of entity network structure",
                score=0,
                weight=self.weights.get("network_centrality", 0.3),
                evidence=["Insufficient network data"]
            )
        
        # Check for highly central nodes
        centrality = nx.degree_centrality(graph.graph)
        high_central = [n for n, c in centrality.items() if c > 0.3]
        
        if high_central:
            score += len(high_central) * 15
            evidence.append(f"{len(high_central)} highly central entities")
        
        # Check for multiple components (fragmented network)
        components = nx.number_connected_components(graph.graph)
        if components > 1:
            score += 10
            evidence.append(f"Network split into {components} groups")
        
        # Check for high-degree nodes
        max_degree = max(dict(graph.graph.degree()).values()) if graph.graph else 0
        if max_degree > 5:
            score += 15
            evidence.append(f"Hub with {max_degree} connections")
        
        return RiskFactor(
            name="Network Centrality",
            description="Assessment of entity network structure",
            score=min(score, 100),
            weight=self.weights.get("network_centrality", 0.3),
            evidence=evidence
        )
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score."""
        if score >= 75:
            return RiskLevel.CRITICAL
        elif score >= 50:
            return RiskLevel.HIGH
        elif score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_findings(
        self, 
        factors: List[RiskFactor],
        patterns: PatternReport
    ) -> List[str]:
        """Generate key findings from analysis."""
        findings = []
        
        # Add pattern summary
        if patterns.summary:
            findings.append(patterns.summary)
        
        # Add highest scoring factor
        top_factor = max(factors, key=lambda f: f.score * f.weight)
        if top_factor.score > 30:
            findings.append(
                f"Primary concern: {top_factor.name} "
                f"(score: {top_factor.score:.0f})"
            )
        
        # Add specific findings from high patterns
        for pattern in patterns.patterns[:3]:
            if pattern.significance >= 0.6:
                findings.append(pattern.description)
        
        return findings[:5]  # Limit to 5 findings
    
    def _generate_recommendations(
        self, 
        factors: List[RiskFactor],
        risk_level: RiskLevel
    ) -> List[str]:
        """Generate recommendations based on assessment."""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("Immediate review recommended")
            recommendations.append("Prioritize investigation of central entities")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Detailed analysis recommended")
            recommendations.append("Review temporal clusters for coordinated activity")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Monitor identified patterns")
            recommendations.append("Consider additional data sources")
        else:
            recommendations.append("Continue routine monitoring")
        
        # Factor-specific recommendations
        for factor in factors:
            if factor.score > 50 and factor.name == "Network Centrality":
                recommendations.append("Map relationships of central entities")
            if factor.score > 50 and factor.name == "Temporal Clustering":
                recommendations.append("Analyze timeline for activity patterns")
        
        return recommendations[:4]
