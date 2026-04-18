"""
Configuration settings for the Intel Fusion system.
"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class NLPConfig:
    """NLP pipeline configuration."""
    model_name: str = "en_core_web_sm"
    
    # Entity types to extract
    entity_types: List[str] = field(default_factory=lambda: [
        "PERSON", "ORG", "GPE", "LOC", "DATE", "EVENT", 
        "MONEY", "NORP", "FAC", "PRODUCT", "LAW"
    ])
    
    # Entity type display names and colors
    entity_colors: Dict[str, str] = field(default_factory=lambda: {
        "PERSON": "#FF6B6B",
        "ORG": "#4ECDC4",
        "GPE": "#45B7D1",
        "LOC": "#96CEB4",
        "DATE": "#FFEAA7",
        "EVENT": "#DDA0DD",
        "MONEY": "#98D8C8",
        "NORP": "#F7DC6F",
        "FAC": "#BB8FCE",
        "PRODUCT": "#85C1E9",
        "LAW": "#F8B500"
    })
    
    entity_labels: Dict[str, str] = field(default_factory=lambda: {
        "PERSON": "Person",
        "ORG": "Organization",
        "GPE": "Location (Political)",
        "LOC": "Location",
        "DATE": "Date",
        "EVENT": "Event",
        "MONEY": "Money",
        "NORP": "Group/Nationality",
        "FAC": "Facility",
        "PRODUCT": "Product",
        "LAW": "Law/Regulation"
    })


@dataclass
class AnalysisConfig:
    """Analysis engine configuration."""
    # Pattern detection thresholds
    frequency_threshold: int = 3  # Min occurrences to flag
    co_occurrence_threshold: int = 2  # Min co-occurrences for relationship
    
    # Risk scoring weights
    risk_weights: Dict[str, float] = field(default_factory=lambda: {
        "entity_density": 0.2,
        "unusual_patterns": 0.3,
        "temporal_clustering": 0.2,
        "network_centrality": 0.3
    })
    
    # Anomaly detection
    anomaly_std_threshold: float = 2.0  # Standard deviations for anomaly


@dataclass
class UIConfig:
    """UI configuration."""
    page_title: str = "Intel Fusion DSS"
    page_icon: str = "🔍"
    layout: str = "wide"
    
    # Graph visualization
    graph_height: int = 600
    timeline_height: int = 400
    
    # Color scheme
    primary_color: str = "#1f77b4"
    background_color: str = "#0e1117"
    secondary_background: str = "#262730"


# Global config instances
nlp_config = NLPConfig()
analysis_config = AnalysisConfig()
ui_config = UIConfig()
