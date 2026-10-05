<<<<<<< HEAD
🔍 Intel Fusion DSS — AI-Powered Intelligence Fusion & Decision Support System
Intel Fusion is a Streamlit-based web application designed to analyze unstructured documents and extract actionable intelligence from them. It's built for intelligence analysts, researchers, or investigators who need to process multiple documents and surface hidden patterns, relationships, and risk signals.

What It Does
Users upload documents (PDF, DOCX, TXT, CSV, XLSX, HTML) and the system runs them through a multi-stage AI pipeline:

Text Extraction — Parses the raw content from supported file formats.
NLP Entity Extraction — Uses spaCy to identify named entities: people, organizations, locations, dates, and events.
Relationship Mapping — Detects co-occurrence relationships between entities within the same sentence and builds a network graph.
Timeline Construction — Extracts temporal events and sequences them chronologically.
Pattern Detection — Finds anomalies, unusual clusters, and hub entities across the knowledge graph.
Risk Assessment — Scores the intelligence across four dimensions (entity density, unusual patterns, temporal clustering, network centrality) to produce an overall risk level: Low → Medium → High → Critical.


Dashboard Tabs
TabWhat It Shows🌐 NetworkInteractive entity relationship graph + frequency charts📅 TimelineChronological event viewer🗺 Geo MapPlotly map of extracted locations (GPE/LOC entities)🔍 InsightsRisk gauge, risk factor breakdown, key findings & recommendations🔎 ExplorerBrowse entities and drill into specific relationships with context

Tech Stack

Frontend/App: Streamlit (dark-themed UI)
NLP: spaCy (en_core_web_sm)
Graph Analysis: NetworkX
Visualizations: Plotly
Document Parsing: PyMuPDF, PyPDF2, python-docx, BeautifulSoup, openpyxl
Geocoding: geopy
=======
🔍 Intel Fusion DSS — AI-Powered Intelligence Fusion & Decision Support System
Intel Fusion is a Streamlit-based web application designed to analyze unstructured documents and extract actionable intelligence from them. It's built for intelligence analysts, researchers, or investigators who need to process multiple documents and surface hidden patterns, relationships, and risk signals.

What It Does
Users upload documents (PDF, DOCX, TXT, CSV, XLSX, HTML) and the system runs them through a multi-stage AI pipeline:

Text Extraction — Parses the raw content from supported file formats.
NLP Entity Extraction — Uses spaCy to identify named entities: people, organizations, locations, dates, and events.
Relationship Mapping — Detects co-occurrence relationships between entities within the same sentence and builds a network graph.
Timeline Construction — Extracts temporal events and sequences them chronologically.
Pattern Detection — Finds anomalies, unusual clusters, and hub entities across the knowledge graph.
Risk Assessment — Scores the intelligence across four dimensions (entity density, unusual patterns, temporal clustering, network centrality) to produce an overall risk level: Low → Medium → High → Critical.


Dashboard Tabs
TabWhat It Shows🌐 NetworkInteractive entity relationship graph + frequency charts📅 TimelineChronological event viewer🗺 Geo MapPlotly map of extracted locations (GPE/LOC entities)🔍 InsightsRisk gauge, risk factor breakdown, key findings & recommendations🔎 ExplorerBrowse entities and drill into specific relationships with context

Tech Stack

Frontend/App: Streamlit (dark-themed UI)
NLP: spaCy (en_core_web_sm)
Graph Analysis: NetworkX
Visualizations: Plotly
Document Parsing: PyMuPDF, PyPDF2, python-docx, BeautifulSoup, openpyxl
Geocoding: geopy
>>>>>>> 256829eadb9bd5681300ade00ce96d7d17c0dc30
