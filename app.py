"""
Intel Fusion DSS - Main Streamlit Application

An AI-powered intelligence fusion and decision support system
for analyzing unstructured documents.
"""
from ui.geomap import create_geo_map
import streamlit as st
from datetime import datetime

# Import core modules
from core.extractor import extract_pdf
from core.nlp_pipeline import NLPPipeline
from core.pattern_detector import PatternDetector
from core.risk_scorer import RiskScorer

# Import data store
from data.store import get_state, reset_state

# Import UI components
from ui.components import (
    render_metric_cards,
    render_insight_panel,
    render_entity_explorer,
    render_document_list
)
from ui.visualizations import (
    create_network_graph,
    create_timeline_chart,
    create_entity_frequency_chart,
    create_risk_gauge,
    create_risk_factors_chart,
    create_entity_type_pie
)

from config import ui_config

# Page configuration
st.set_page_config(
    page_title=ui_config.page_title,
    page_icon=ui_config.page_icon,
    layout=ui_config.layout,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid #333;
    }
    
    .main-header h1 {
        margin: 0;
        color: #4ECDC4;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: #888;
        margin-top: 0.5rem;
    }
    
    .upload-section {
        background: #1e1e2e;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #333;
        text-align: center;
    }
    
    .stExpander {
        background-color: #1e1e2e;
        border: 1px solid #333;
    }
    
    div[data-testid="metric-container"] {
        background-color: #1e1e2e;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #333;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e2e;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4ECDC4 !important;
        color: #000 !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Initialize state
    state = get_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Intel Fusion DSS</h1>
        <p>AI-Powered Intelligence Fusion & Decision Support System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🧠 Intel Fusion")
        st.caption("AI Decision Support System")

        st.markdown("---")

        uploaded_files = st.file_uploader(
            "📄 Upload PDF documents",
            type=["pdf"],
            accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("🚀 Process Documents", type="primary", use_container_width=True):
                process_documents(uploaded_files, state)

        st.markdown("---")

        if state.has_data:
            st.success(f"{state.document_count} document(s) loaded")

            if st.button("🗑️ Clear Data", use_container_width=True):
                reset_state()
                st.rerun()

        st.markdown("---")

        if state.documents:
            render_document_list(state.documents)
        
    # Main content
    if not state.has_data:
        render_welcome_screen()
    else:
        render_analysis_dashboard(state)


def process_documents(uploaded_files, state):
    """Process uploaded documents through the pipeline."""
    
    # Initialize pipeline
    nlp_pipeline = NLPPipeline()
    
    progress = st.progress(0)
    status = st.status("Processing documents...", expanded=True)
    
    total_files = len(uploaded_files)
    
    for idx, file in enumerate(uploaded_files):
        status.write(f"📄 Processing: {file.name}")
        
        try:
            # Extract text
            status.write("  ├─ Extracting text...")
            doc = extract_pdf(file.read(), file.name)
            
            # NLP processing
            status.write("  ├─ Extracting entities and relationships...")
            extraction = nlp_pipeline.process(doc.full_text, doc.id)
            
            # Add to state
            status.write("  └─ Building knowledge graph...")
            state.add_document(doc, extraction)
            
            status.write(f"  ✅ Extracted {len(extraction.entities)} entities")
            
        except Exception as e:
            status.write(f"  ❌ Error: {str(e)}")
        
        progress.progress((idx + 1) / total_files)
    
    # Run pattern detection
    status.write("🔍 Detecting patterns and anomalies...")
    detector = PatternDetector()
    state.pattern_report = detector.analyze(
        state.graph,
        state.timeline,
        state.extractions
    )
    
    # Run risk assessment
    status.write("⚖️ Calculating risk assessment...")
    scorer = RiskScorer()
    state.risk_assessment = scorer.assess(
        state.graph,
        state.timeline,
        state.pattern_report
    )
    
    status.update(label="✅ Processing complete!", state="complete")
    progress.empty()
    
    st.rerun()


def render_welcome_screen():
    """Render the welcome screen when no data is loaded."""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h2>Welcome to Intel Fusion</h2>
            <p style="color: #888; margin-bottom: 2rem;">
                Upload PDF documents to extract intelligence, detect patterns,
                and generate actionable insights.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Capabilities")
        
        capabilities = [
            ("🏷️ Entity Extraction", "Identify people, organizations, locations, and dates"),
            ("🔗 Relationship Mapping", "Discover connections between entities"),
            ("📅 Timeline Analysis", "Sequence events chronologically"),
            ("🔍 Pattern Detection", "Find anomalies and unusual patterns"),
            ("⚖️ Risk Assessment", "Calculate intelligence risk scores"),
            ("📈 Interactive Visualizations", "Explore data through graphs and charts")
        ]
        
        for title, desc in capabilities:
            st.markdown(f"**{title}**  \n{desc}")


def render_analysis_dashboard(state):
    """Render the main analysis dashboard."""
    
    # # Metrics row
    # metrics = state.to_summary()
    # render_metric_cards(metrics)
    
    st.divider()
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Entities", len(state.graph.graph.nodes))
    col2.metric("Relationships", len(state.graph.graph.edges))
    col3.metric("Documents", state.document_count)
    col4.metric("Events", len(state.timeline.entries))
    
    # Main tabs
    tab_network, tab_timeline, tab_map, tab_insights, tab_explore = st.tabs([
        "🌐 Network",
        "📅 Timeline",
        "🗺 Geo Map",
        "🔍 Insights",
        "🔎 Explorer"
    ])
    
    with tab_network:
        render_network_tab(state)
    
    with tab_timeline:
        render_timeline_tab(state)
    
    with tab_insights:
        render_insights_tab(state)
    
    with tab_map:
        render_map_tab(state)
    
    with tab_explore:
        render_explorer_tab(state)

def render_map_tab(state):
    """Render geo map tab."""

    st.subheader("🗺 Geographical Intelligence")

    locations = []

    for extraction in state.extractions:
        for ent in extraction.entities:
            if ent.label in ["GPE", "LOC"]:
                locations.append(ent.text)

    if locations:
        fig = create_geo_map(locations)

        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not generate map from extracted locations.")
    else:
        st.info("No location data found.")

def render_network_tab(state):
    """Render the network visualization tab."""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Network graph
        fig = create_network_graph(state.graph)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Graph metrics
        metrics = state.graph.get_metrics()
        
        st.markdown("### 📊 Network Stats")
        st.metric("Nodes", metrics.node_count)
        st.metric("Edges", metrics.edge_count)
        st.metric("Density", f"{metrics.density:.3f}")
        st.metric("Components", metrics.components)
        
        if metrics.most_connected:
            st.markdown("### 🔗 Most Connected")
            for node, degree in metrics.most_connected[:5]:
                st.markdown(f"- **{node}** ({degree})")
    
    # Entity distribution
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Frequency chart
        entity_counts = {}
        for extraction in state.extractions:
            for label, counts in extraction.entity_counts.items():
                if label not in entity_counts:
                    entity_counts[label] = {}
                for entity, count in counts.items():
                    entity_counts[label][entity] = entity_counts[label].get(entity, 0) + count
        
        fig = create_entity_frequency_chart(entity_counts)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Type distribution
        fig = create_entity_type_pie(entity_counts)
        st.plotly_chart(fig, use_container_width=True)


def render_timeline_tab(state):
    """Render the timeline visualization tab."""
    
    timeline = state.timeline
    
    # Timeline chart
    fig = create_timeline_chart(timeline)
    st.plotly_chart(fig, use_container_width=True)
    
    # Timeline details
    if timeline.entries:
        st.divider()
        
        st.markdown("### 📋 Event Details")
        
        for entry in timeline.entries:
            with st.expander(f"📅 {entry.date_display} ({len(entry.events)} events)"):
                for event in entry.events[:5]:
                    st.markdown(f"- {event[:200]}{'...' if len(event) > 200 else ''}")
                
                if entry.entities:
                    st.markdown(f"**Entities:** {', '.join(entry.entities[:10])}")
    else:
        st.info("No dated events found in the documents. Timeline requires documents with specific dates.")


def render_insights_tab(state):
    """Render the insights and risk assessment tab."""
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Risk gauge
        if state.risk_assessment:
            st.markdown("### ⚖️ Risk Assessment")
            fig = create_risk_gauge(state.risk_assessment)
            st.plotly_chart(fig, use_container_width=True)
            
            fig = create_risk_factors_chart(state.risk_assessment)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Insight panel
        if state.pattern_report:
            render_insight_panel(state.pattern_report, state.risk_assessment)


def render_explorer_tab(state):
    """Render the entity explorer tab."""
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_entity_explorer(state.graph)
    
    with col2:
        st.subheader("🔗 Relationship Details")
        
        # Get relationships
        relationships = []
        for u, v, data in state.graph.graph.edges(data=True):
            relationships.append({
                "source": u,
                "target": v,
                "weight": data.get("weight", 1),
                "contexts": data.get("contexts", [])
            })
        
        relationships.sort(key=lambda x: x["weight"], reverse=True)
        
        for rel in relationships[:15]:
            with st.expander(
                f"**{rel['source']}** ↔ **{rel['target']}** ({rel['weight']})",
                expanded=False
            ):
                if rel["contexts"]:
                    st.caption("Context sentences:")
                    for ctx in rel["contexts"][:2]:
                        st.markdown(f"> {ctx[:200]}...")


if __name__ == "__main__":
    main()
