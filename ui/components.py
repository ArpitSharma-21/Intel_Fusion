"""
Reusable UI components for the Streamlit dashboard.
"""
import streamlit as st
from typing import List, Dict, Any, Optional

from core.pattern_detector import Pattern, Anomaly, PatternReport
from core.risk_scorer import RiskAssessment, RiskLevel
from core.graph_builder import IntelGraph
from config import nlp_config


def render_metric_cards(metrics: Dict[str, Any]):
    """Render a row of metric cards."""
    cols = st.columns(4)
    
    with cols[0]:
        st.metric(
            "📄 Documents",
            metrics.get("documents", 0)
        )
    
    with cols[1]:
        st.metric(
            "🏷️ Entities",
            metrics.get("entities", 0)
        )
    
    with cols[2]:
        st.metric(
            "🔗 Relationships",
            metrics.get("relationships", 0)
        )
    
    with cols[3]:
        st.metric(
            "📅 Events",
            metrics.get("events", 0)
        )


def render_pattern_card(pattern: Pattern):
    """Render a single pattern as an expandable card."""
    # Significance indicator
    if pattern.significance >= 0.7:
        icon = "🔴"
        badge = "High"
    elif pattern.significance >= 0.4:
        icon = "🟡"
        badge = "Medium"
    else:
        icon = "🟢"
        badge = "Low"
    
    with st.expander(f"{icon} {pattern.description}", expanded=False):
        st.caption(f"**Type:** {pattern.pattern_type.replace('_', ' ').title()}")
        st.caption(f"**Significance:** {badge} ({pattern.significance:.0%})")
        
        if pattern.entities_involved:
            st.write("**Entities involved:**")
            entity_tags = " ".join([f"`{e}`" for e in pattern.entities_involved[:8]])
            st.markdown(entity_tags)
        
        if pattern.evidence:
            st.write("**Evidence:**")
            for ev in pattern.evidence[:5]:
                st.markdown(f"- {ev}")
        
        if pattern.recommendation:
            st.info(f"💡 {pattern.recommendation}")


def render_anomaly_card(anomaly: Anomaly):
    """Render a single anomaly alert."""
    severity_colors = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }
    
    icon = severity_colors.get(anomaly.severity, "⚪")
    
    with st.expander(f"{icon} {anomaly.description}", expanded=anomaly.severity == "high"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Expected", f"{anomaly.expected_value:.1f}")
        with col2:
            st.metric("Actual", f"{anomaly.actual_value:.0f}")
        
        st.caption(f"Deviation: {anomaly.deviation:+.1f} standard deviations")


def render_insight_panel(
    patterns: PatternReport,
    risk: Optional[RiskAssessment] = None
):
    """Render the insight panel with findings and recommendations."""
    st.subheader("🎯 Key Insights")
    
    # Risk overview
    if risk:
        render_risk_overview(risk)
    
    # Summary
    if patterns.summary:
        st.info(patterns.summary)
    
    # Patterns
    st.write("### 🔍 Detected Patterns")
    
    if patterns.patterns:
        for pattern in patterns.patterns[:5]:
            render_pattern_card(pattern)
    else:
        st.caption("No significant patterns detected.")
    
    # Anomalies
    if patterns.anomalies:
        st.write("### ⚠️ Anomalies")
        for anomaly in patterns.anomalies[:3]:
            render_anomaly_card(anomaly)
    
    # Recommendations
    if risk and risk.recommendations:
        st.write("### 💡 Recommendations")
        for rec in risk.recommendations:
            st.markdown(f"- {rec}")


def render_risk_overview(risk: RiskAssessment):
    """Render risk score overview."""
    level_colors = {
        RiskLevel.LOW: ("green", "✅"),
        RiskLevel.MEDIUM: ("orange", "⚠️"),
        RiskLevel.HIGH: ("red", "🔶"),
        RiskLevel.CRITICAL: ("red", "🔴")
    }
    
    color, icon = level_colors.get(risk.risk_level, ("gray", "❓"))
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(30,30,30,0.9), rgba(50,50,50,0.9));
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid {color};
        margin-bottom: 20px;
    ">
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 2.5rem;">{icon}</span>
            <div>
                <div style="font-size: 2rem; font-weight: bold; color: {color};">
                    {risk.overall_score:.0f}
                </div>
                <div style="color: #888; font-size: 0.9rem;">
                    Risk Level: {risk.risk_level.value.upper()}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_entity_explorer(graph: IntelGraph):
    """Render entity exploration interface."""
    st.subheader("🔎 Entity Explorer")
    
    # Get all entities grouped by type
    entities_by_type = {}
    for node, data in graph.graph.nodes(data=True):
        entity_type = data.get("label", "OTHER")
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append({
            "name": node,
            "count": data.get("count", 1),
            "connections": graph.graph.degree(node)
        })
    
    if not entities_by_type:
        st.caption("No entities to explore.")
        return
    
    # Type filter
    selected_type = st.selectbox(
        "Filter by type",
        ["All"] + list(entities_by_type.keys()),
        format_func=lambda x: nlp_config.entity_labels.get(x, x) if x != "All" else "All Types"
    )
    
    # Display entities
    if selected_type == "All":
        display_entities = []
        for entities in entities_by_type.values():
            display_entities.extend(entities)
    else:
        display_entities = entities_by_type.get(selected_type, [])
    
    # Sort by connections
    display_entities.sort(key=lambda x: x["connections"], reverse=True)
    
    # Render as table
    for entity in display_entities[:20]:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{entity['name']}**")
        with col2:
            st.caption(f"📊 {entity['count']}")
        with col3:
            st.caption(f"🔗 {entity['connections']}")


def render_document_list(documents: List[Any]):
    """Render list of uploaded documents."""
    st.subheader("📁 Documents")
    
    for doc in documents:
        with st.expander(f"📄 {doc.filename}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Pages", doc.total_pages)
            with col2:
                st.metric("Words", f"{doc.total_words:,}")
            with col3:
                st.metric("ID", doc.id[:8])
            
            st.write("**Preview:**")
            st.text(doc.preview)
