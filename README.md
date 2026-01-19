🧠 README — Daryn’s MCP Ecosystem (Cognitive Loop + Knowledge Graph)
A complete reference for architecture, tools, flows, and usage

📌 Overview
You have built a multi‑agent, multi‑MCP cognitive system composed of:
1. Cognitive Loop MCP (v0.5)
A persistent, stateful reasoning engine that:
• 	reads the Knowledge Graph
• 	reads long‑term memory
• 	reflects
• 	writes new nodes/edges
• 	updates its own cognitive state
• 	maintains continuity across cycles
2. Knowledge Graph MCP (v0.5)
A SQLite‑backed graph server that stores:
• 	nodes
• 	edges
• 	cognitive state
• 	reflection chains
• 	insights
• 	actions
Together, they form a self‑maintaining cognitive substrate.

🧩 Architecture Summary


🧠 Cognitive Loop MCP (v0.5)
Tools
1. run_cycle
Generates a read plan:
• 	list_recent_nodes
• 	list_recent_edges
• 	list_memories
• 	find_or_create_state_node
2. reflect
Consumes:
• 	nodes
• 	edges
• 	memories
• 	cognitive_state
Produces:
• 	reflection text
• 	summary
3. apply_insights
Consumes:
• 	reflection
• 	summary
• 	state_node_id
• 	state
Produces:
• 	write_plan (add_node, add_edge, update_state_node)
• 	updated_state
4. heartbeat
Returns:
• 	current cognitive state
• 	last cycle
• 	last reflection
• 	last summary

🧩 Knowledge Graph MCP (v0.5)
Tools
1. add_node
Creates a node:
• 	label
• 	type
• 	data
2. add_edge
Creates an edge:
• 	source_id
• 	target_id
• 	relation
• 	data
3. list_recent_nodes
Returns latest nodes.
4. list_recent_edges
Returns latest edges.
5. find_or_create_state_node
Searches for:

If missing → creates it with default state.
6. update_node_data
Updates the cognitive_state node with:
• 	cycle_count
• 	last_cycle_time
• 	last_reflection
• 	last_summary
• 	last_active_concepts
• 	etc.

🔄 Full v0.5 Cognitive Cycle (Step‑by‑Step)
1. Trigger the cycle

You get a read plan.

2. Execute the read plan
Run each call:


3. Reflect


4. Apply insights

You get a write plan.

5. Execute the write plan


6. Inspect the graph

You will see:
• 	Reflection node
• 	Insight node
• 	Action node
• 	Updated cognitive_state node

🧠 Cognitive State Node Structure
Stored inside the Knowledge Graph:

This node evolves every cycle.

🧩 File Locations
Cognitive Loop MCP

Knowledge Graph MCP

SQLite DB


⚙️ LM Studio MCP Configuration


🛠 Debugging Checklist
If  returns :
• 	LM Studio is running an old cached MCP
• 	Restart LM Studio
• 	Ensure correct Python path
If KG tools fail:
• 	KG MCP didn’t start
• 	DB path invalid
• 	Python interpreter wrong
• 	Syntax error in KG server
If state node doesn’t update:
• 	 not implemented
• 	Wrong node_id passed
