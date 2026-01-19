🧠 README — Daryn’s Multi‑MCP Cognitive Architecture
A complete reference for your Cognitive Loop, Knowledge Graph, Long‑Term Memory, Python‑Lab, Paperless, Web‑Search, and ZIM MCPs.

1. Introduction
This repository defines a multi‑agent cognitive system built entirely on MCP (Model Context Protocol) servers. Each MCP provides a specialized capability — structured memory, semantic memory, document ingestion, Python execution, web search, offline knowledge, and autonomous reasoning.
Together, these MCPs form a unified cognitive substrate capable of:
• 	ingesting documents
• 	extracting and structuring knowledge
• 	storing long‑term memories
• 	performing semantic search
• 	running autonomous cognitive cycles
• 	generating reflections and insights
• 	evolving its internal state over time
This README documents the architecture, tools, data flows, and usage patterns for the entire system.

2. System Architecture (Narrative Format)
Your system is composed of several cooperating MCP servers. Each one exposes tools through LM Studio, and the Cognitive Loop orchestrates them into a coherent reasoning engine.
2.1 Cognitive Loop MCP (v0.5)
The Cognitive Loop is the reasoning core of the system. It performs autonomous cycles that read from the graph, read long‑term memory, generate reflections, write insights, and update its own persistent cognitive state.
Responsibilities:
• 	Initiate cognitive cycles
• 	Generate reflections and insights
• 	Maintain a persistent cognitive_state node
• 	Write new knowledge into the graph
• 	Coordinate with other MCPs
Tools:
• 	
• 	
• 	
• 	

2.2 Knowledge Graph MCP (v0.5)
The Knowledge Graph is the structured memory store. It uses SQLite to store nodes, edges, reflections, insights, actions, and the cognitive_state node.
Responsibilities:
• 	Store concepts, documents, reflections, insights
• 	Maintain graph structure
• 	Persist the cognitive loop’s state
• 	Provide recent activity for reflection
Tools:
• 	
• 	
• 	
• 	
• 	
• 	

2.3 Long‑Term Memory MCP
This subsystem stores semantic memories (text + embeddings) and supports similarity search.
Responsibilities:
• 	Store memories with embeddings
• 	Retrieve memories via semantic search
• 	Provide episodic memory to the Cognitive Loop
Tools:
• 	
• 	
• 	

2.4 Python‑Lab MCP
A sandboxed Python execution environment for safe computation and analysis.
Responsibilities:
• 	Execute Python code safely
• 	Perform data transformations
• 	Compute embeddings or statistics
• 	Support document or text analysis
Tools:
• 	

2.5 Paperless MCP
A document ingestion and OCR subsystem connected to your Paperless‑NGX instance.
Responsibilities:
• 	List documents
• 	Retrieve documents
• 	Extract text
• 	Provide metadata
Tools:
• 	
• 	
• 	
• 	

2.6 Web‑Search MCP
Provides external information retrieval from the internet.
Responsibilities:
• 	Perform web searches
• 	Provide fresh information
• 	Support concept enrichment
Tools:
• 	

2.7 ZIM MCP
Provides offline encyclopedia‑style knowledge from ZIM archives.
Responsibilities:
• 	Search ZIM archives
• 	Retrieve article content
• 	Provide offline fallback knowledge
Tools:
• 	
• 	

3. Cognitive Loop v0.5 — Full Cycle Overview
A v0.5 cognitive cycle consists of six phases:
3.1 Initiation
The loop begins with:

This returns a read plan.

3.2 Reading
The host executes:
• 	
• 	
• 	
• 	
This provides the loop with:
• 	recent graph activity
• 	recent memories
• 	its persistent cognitive state

3.3 Reflection
The loop synthesizes the inputs:

This produces:
• 	reflection text
• 	summary
• 	concept activity
• 	cycle‑aware insights

3.4 Insight Generation
The loop converts reflection into actionable graph updates:

This returns a write plan.

3.5 Writing
The host executes:
• 	 (reflection)
• 	 (insight)
• 	 (action)
• 	 (cognitive_state)
This updates the graph and the loop’s persistent state.

3.6 Inspection
You can inspect the results:

You will see:
• 	a new reflection node
• 	a new insight node
• 	a new action node
• 	an updated cognitive_state node

4. Cognitive State Node Structure
The Knowledge Graph stores the loop’s persistent state as:

This evolves every cycle.

5. File Locations
Cognitive Loop MCP

Knowledge Graph MCP

SQLite DB


6. LM Studio MCP Configuration
Your corrected configuration uses explicit Python paths:


7. Debugging Guide
If  returns 
• 	LM Studio is running a cached MCP
• 	Restart LM Studio
• 	Ensure correct Python path
If KG tools fail
• 	KG MCP didn’t start
• 	DB path invalid
• 	Python interpreter wrong
If state node doesn’t update
• 	Wrong node_id
• 	update_node_data not implemented

8. Future Extensions
You can extend this architecture with:
• 	nightly autonomous cognition
• 	concept clustering
• 	document tagging
• 	multi‑agent reasoning
• 	long‑term planning
• 	self‑improving reflection loops
• 	cross‑MCP orchestration
