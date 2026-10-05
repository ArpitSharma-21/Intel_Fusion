"""
Visualization components using Plotly.
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from typing import List, Dict, Optional, Tuple
import math

from core.graph_builder import IntelGraph
from core.timeline_builder import Timeline, TimelineEntry
from core.pattern_detector import PatternReport
from core.risk_scorer import RiskAssessment, RiskLevel
from config import nlp_config, ui_config


def create_network_graph(
    graph: IntelGraph,
    highlight_nodes: Optional[List[str]] = None,
    show_labels: bool = True
) -> go.Figure:
    """
    Create an interactive network visualization.
    
    Args:
        graph: The intelligence graph to visualize
        highlight_nodes: Nodes to highlight
        show_labels: Whether to show node labels
        
    Returns:
        Plotly figure
    """
    G = graph.graph
    
    if len(G) == 0:
        # Empty graph placeholder
        fig = go.Figure()
        fig.add_annotation(
            text="No entities to display.<br>Upload documents to build the network.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#888")
        )
        fig.update_layout(
            height=ui_config.graph_height,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # Calculate layout
    if len(G) < 50:
        pos = nx.spring_layout(G, k=2/math.sqrt(len(G)), iterations=50, seed=42)
    else:
        pos = nx.kamada_kawai_layout(G)
    
    # Create edge traces
    edge_traces = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        weight = edge[2].get('weight', 1)
        
        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(
                width=min(weight, 5),
                color='rgba(150, 150, 150, 0.5)'
            ),
            hoverinfo='none',
            showlegend=False
        ))
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Node data
        data = G.nodes[node]
        label = data.get('label', 'UNKNOWN')
        count = data.get('count', 1)
        
        # Color by type
        color = nlp_config.entity_colors.get(label, '#888888')
        node_color.append(color)
        
        # Size by count/degree
        degree = G.degree(node)
        size = 10 + min(count * 2, 20) + min(degree * 2, 20)
        node_size.append(size)
        
        # Hover text
        label_name = nlp_config.entity_labels.get(label, label)
        node_text.append(
            f"<b>{node}</b><br>"
            f"Type: {label_name}<br>"
            f"Mentions: {count}<br>"
            f"Connections: {degree}"
        )
    
    # Highlight effect
    node_line_width = [
        3 if highlight_nodes and node in highlight_nodes else 0
        for node in G.nodes()
    ]
    
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text' if show_labels and len(G) < 30 else 'markers',
        hoverinfo='text',
        text=[node for node in G.nodes()] if show_labels else None,
        textposition='top center',
        textfont=dict(size=9, color='white'),
        hovertext=node_text,
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(
                width=node_line_width,
                color='white'
            )
        ),
        showlegend=False
    )
    
    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])
    
    # Add legend for entity types
    for label, color in nlp_config.entity_colors.items():
        if any(G.nodes[n].get('label') == label for n in G.nodes()):
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color=color),
                name=nlp_config.entity_labels.get(label, label),
                showlegend=True
            ))
    
    fig.update_layout(
        title=dict(
            text="Entity Relationship Network",
            font=dict(size=16, color='white')
        ),
        height=ui_config.graph_height,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(color='white')
        ),
        hovermode='closest',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def create_timeline_chart(timeline: Timeline) -> go.Figure:
    """
    Create an interactive timeline visualization.
    """
    if not timeline.entries:
        fig = go.Figure()
        fig.add_annotation(
            text="No dated events found.<br>Upload documents with dates to build timeline.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#888")
        )
        fig.update_layout(
            height=ui_config.timeline_height,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # Prepare data
    dates = [entry.date for entry in timeline.entries]
    importance = [entry.importance for entry in timeline.entries]
    
    # Create hover text
    hover_text = []
    for entry in timeline.entries:
        text = f"<b>{entry.date_display}</b><br><br>"
        for event in entry.events[:3]:
            if len(event) > 100:
                event = event[:100] + "..."
            text += f"• {event}<br>"
        if len(entry.events) > 3:
            text += f"<i>...and {len(entry.events) - 3} more</i><br>"
        if entry.entities:
            text += f"<br>Entities: {', '.join(entry.entities[:5])}"
        hover_text.append(text)
    
    fig = go.Figure()
    
    # Add event markers
    fig.add_trace(go.Scatter(
        x=dates,
        y=[1] * len(dates),
        mode='markers+text',
        marker=dict(
            size=[10 + i * 3 for i in importance],
            color='#4ECDC4',
            symbol='circle',
            line=dict(width=2, color='white')
        ),
        text=[entry.date_display for entry in timeline.entries],
        textposition='top center',
        textfont=dict(size=10, color='white'),
        hovertext=hover_text,
        hoverinfo='text',
        showlegend=False
    ))
    
    # Add connecting line
    fig.add_trace(go.Scatter(
        x=dates,
        y=[1] * len(dates),
        mode='lines',
        line=dict(color='rgba(78, 205, 196, 0.3)', width=2),
        hoverinfo='none',
        showlegend=False
    ))
    
    fig.update_layout(
        title=dict(
            text="Event Timeline",
            font=dict(size=16, color='white') # Use 'font' not 'titlefont'
        ),
        height=ui_config.timeline_height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title=dict(
                text="Date",
                font=dict(color='white') # Use 'font' inside 'title'
            ),
            tickfont=dict(color='white'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)' # Gridcolor is a direct axis property
        ),
        yaxis=dict(
            visible=False,
            range=[0.5, 1.8]
        ),
        margin=dict(l=20, r=20, t=40, b=40),
        hovermode='closest'
    )
    
    return fig


def create_entity_frequency_chart(
    entity_counts: Dict[str, Dict[str, int]],
    top_n: int = 15
) -> go.Figure:
    """
    Create a bar chart of entity frequencies by type.
    """
    # Flatten and sort
    all_entities = []
    for entity_type, entities in entity_counts.items():
        for entity, count in entities.items():
            all_entities.append({
                "entity": entity,
                "count": count,
                "type": entity_type,
                "color": nlp_config.entity_colors.get(entity_type, "#888")
            })
    
    if not all_entities:
        fig = go.Figure()
        fig.add_annotation(
            text="No entities to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Sort and take top N
    sorted_entities = sorted(all_entities, key=lambda x: x["count"], reverse=True)[:top_n]
    
    fig = go.Figure(go.Bar(
        x=[e["entity"] for e in sorted_entities],
        y=[e["count"] for e in sorted_entities],
        marker_color=[e["color"] for e in sorted_entities],
        text=[e["count"] for e in sorted_entities],
        textposition='auto',
        hovertemplate="<b>%{x}</b><br>Mentions: %{y}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="Top Entity Mentions",
            font=dict(size=14, color='white') # Changed from titlefont
        ),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickangle=45,
            tickfont=dict(color='white', size=10),
            showgrid=False
        ),
        yaxis=dict(
            title=dict(
                text="Mentions",
                font=dict(color='white') # Use 'font' inside 'title'
            ),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)' # Moved gridcolor out of title
        ),
        margin=dict(l=40, r=20, t=40, b=80)
    )
    
    return fig


def create_risk_factors_chart(assessment: RiskAssessment) -> go.Figure:
    """
    Create a bar chart showing individual risk factors.
    """
    factors = assessment.factors
    
    fig = go.Figure(go.Bar(
        y=[f.name for f in factors],
        x=[f.score for f in factors],
        orientation='h',
        marker_color=['#3498db', '#9b59b6', '#1abc9c', '#e74c3c'][:len(factors)],
        text=[f"{f.score:.0f}" for f in factors],
        textposition='auto',
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="Risk Factor Breakdown",
            font=dict(size=14, color='white') # Fixed: used 'font'
        ),
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title=dict(
                text="Score",
                font=dict(color='white') # Fixed: used 'font' inside 'title'
            ),
            range=[0, 100],
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)' # Fixed: moved out of title
        ),
        yaxis=dict(
            tickfont=dict(color='white')
        ),
        margin=dict(l=120, r=20, t=40, b=40)
    )
    
    return fig

def create_risk_gauge(assessment: RiskAssessment) -> go.Figure:
    """
    Create a gauge chart showing overall risk score.
    """
    colors = {
        RiskLevel.LOW: "#2ecc71",
        RiskLevel.MEDIUM: "#f1c40f",
        RiskLevel.HIGH: "#e67e22",
        RiskLevel.CRITICAL: "#e74c3c"
    }
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=assessment.overall_score,
        title=dict(
            text=f"Risk Level: {assessment.risk_level.value.upper()}",
            font=dict(size=16, color='white') # Fixed: used 'font'
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickfont=dict(color='white')
            ),
            bar=dict(color=colors[assessment.risk_level]),
            bgcolor='rgba(255,255,255,0.1)',
            borderwidth=0,
            steps=[
                dict(range=[0, 25], color='rgba(46, 204, 113, 0.3)'),
                dict(range=[25, 50], color='rgba(241, 196, 15, 0.3)'),
                dict(range=[50, 75], color='rgba(230, 126, 34, 0.3)'),
                dict(range=[75, 100], color='rgba(231, 76, 60, 0.3)')
            ],
            threshold=dict(
                line=dict(color='white', width=2),
                thickness=0.75,
                value=assessment.overall_score
            )
        ),
        number=dict(font=dict(color='white', size=40))
    ))
    
    fig.update_layout(
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=50, b=20)
    )
    
    return fig

def create_entity_type_pie(entity_counts: Dict[str, Dict[str, int]]) -> go.Figure:
    """
    Create a pie chart showing entity type distribution.
    
    Args:
        entity_counts: Dict of {entity_type: {entity: count}}
        
    Returns:
        Plotly figure
    """
    type_totals = {}
    for entity_type, entities in entity_counts.items():
        type_totals[entity_type] = sum(entities.values())
    
    if not type_totals:
        fig = go.Figure()
        fig.add_annotation(text="No data", x=0.5, y=0.5, showarrow=False)
        return fig
    
    labels = [nlp_config.entity_labels.get(t, t) for t in type_totals.keys()]
    values = list(type_totals.values())
    colors = [nlp_config.entity_colors.get(t, "#888") for t in type_totals.keys()]
    
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.4,
        textinfo='percent+label',
        textfont=dict(size=10, color='white'),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="Entity Types",
            font=dict(size=14, color='white')
        ),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig
