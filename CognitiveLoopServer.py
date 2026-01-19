#!/usr/bin/env python3
import json
import sys
from datetime import datetime

# ------------------------------------------------------------
# JSON-RPC helpers
# ------------------------------------------------------------

def send_message(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

def read_message():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)

# ------------------------------------------------------------
# Persistent Knowledge Graph client (via LM Studio routing)
# ------------------------------------------------------------

class KnowledgeGraphClient:
    """
    v0.5: This is a logical client abstraction.
    In LM Studio, the actual routing to the knowledge-graph MCP
    is handled by the host, so this client is conceptual:
    we describe the calls we want to make, and the host executes them.
    For v0.5, we model this as helper methods that return
    JSON-RPC-style call descriptors.
    """

    def list_recent_nodes(self, limit=20):
        return {
            "call": "knowledge-graph:list_recent_nodes",
            "arguments": {"limit": limit}
        }

    def list_recent_edges(self, limit=20):
        return {
            "call": "knowledge-graph:list_recent_edges",
            "arguments": {"limit": limit}
        }

    def add_node(self, label, type_, data=None):
        return {
            "call": "knowledge-graph:add_node",
            "arguments": {
                "label": label,
                "type": type_,
                "data": data or {}
            }
        }

    def add_edge(self, source_id, target_id, relation, data=None):
        return {
            "call": "knowledge-graph:add_edge",
            "arguments": {
                "source_id": source_id,
                "target_id": target_id,
                "relation": relation,
                "data": data or {}
            }
        }

    def find_state_node(self):
        """
        Conceptual descriptor for: find or create the cognitive_state node.
        The host (agent) is expected to implement this by:
        - searching for a node with type='cognitive_state'
        - or creating one if missing
        For v0.5, we expose this as a high-level intention.
        """
        return {
            "call": "knowledge-graph:find_or_create_state_node",
            "arguments": {
                "label": "Cognitive Loop State",
                "type": "cognitive_state"
            }
        }

KG_CLIENT = KnowledgeGraphClient()

# ------------------------------------------------------------
# Cognitive state model (stored in the Knowledge Graph)
# ------------------------------------------------------------

def default_cognitive_state():
    return {
        "cycle_count": 0,
        "last_cycle_time": None,
        "last_mode": "normal",
        "last_reflection": None,
        "last_summary": None,
        "last_written_nodes": [],
        "last_written_edges": [],
        "last_active_concepts": [],
        "last_memory_snapshot": [],
    }

# ------------------------------------------------------------
# Tool: run_cycle (full autonomous cycle)
# ------------------------------------------------------------

def tool_run_cycle(params):
    """
    v0.5 Cognitive Loop:
    - Full autonomous cycle:
      1) Read graph + memory
      2) Read cognitive state (from KG)
      3) Reflect
      4) Apply insights (write to KG)
      5) Update cognitive state node
    - Returns a high-level plan of what should be executed.
    - The host (agent) is expected to:
      - execute the read calls
      - call `reflect`
      - call `apply_insights`
      - execute the write calls
      - update the state node
    """

    mode = params.get("mode", "normal")

    read_plan = [
        KG_CLIENT.list_recent_nodes(limit=20),
        KG_CLIENT.list_recent_edges(limit=20),
        {
            "call": "long_term_memory:list_memories",
            "arguments": {"limit": 20}
        },
        KG_CLIENT.find_state_node()
    ]

    return {
        "mode": mode,
        "plan": read_plan,
        "message": (
            "v0.5 run_cycle initialized. Execute this read plan, then call `reflect` "
            "with the results, then `apply_insights`, then update the cognitive_state node."
        )
    }

# ------------------------------------------------------------
# Tool: reflect
# ------------------------------------------------------------

def tool_reflect(params):
    """
    Accepts:
        {
            "nodes": [...],
            "edges": [...],
            "memories": [...],
            "state": {...}   # optional cognitive_state data
        }

    Produces:
        - reflection text
        - summary (including cognitive_state-aware info)
    """

    nodes = params.get("nodes", [])
    edges = params.get("edges", [])
    memories = params.get("memories", [])
    state = params.get("state", {}) or default_cognitive_state()

    concepts = [n["label"] for n in nodes if n.get("type") == "concept"]
    documents = [n for n in nodes if n.get("type") == "document"]

    reflection = []

    if nodes:
        reflection.append(f"{len(nodes)} recent nodes are present in the knowledge graph.")
    if edges:
        reflection.append(f"{len(edges)} edges currently link concepts and entities.")
    if concepts:
        reflection.append("Active concepts: " + ", ".join(concepts[:10]))
    if documents:
        reflection.append(f"{len(documents)} document nodes detected.")
    if memories:
        reflection.append(f"{len(memories)} recent memory entries retrieved.")

    if not reflection:
        reflection.append("No recent activity detected across graph or memory.")

    if len(concepts) > 1:
        reflection.append("There is conceptual activity — consider clustering or linking related concepts.")
    if documents:
        reflection.append("Recent documents may need tagging or entity extraction.")
    if edges:
        reflection.append("Graph connectivity is non-zero — consider exploring subgraphs or central nodes.")

    # Incorporate cognitive state
    cycle_count = state.get("cycle_count", 0)
    last_cycle_time = state.get("last_cycle_time")
    if cycle_count > 0:
        reflection.append(
            f"The cognitive loop has run {cycle_count} times. "
            f"Last cycle time: {last_cycle_time}."
        )
    else:
        reflection.append("This appears to be an early or initial cognitive cycle.")

    reflection.append(
        "Suggested next steps: enrich nodes with metadata, add missing edges, "
        "tag documents with relevant concepts, and refine concept clusters over time."
    )

    summary = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "memory_count": len(memories),
        "active_concepts": concepts[:10],
        "cycle_count": cycle_count,
        "last_cycle_time": last_cycle_time,
    }

    return {
        "reflection": " ".join(reflection),
        "summary": summary
    }

# ------------------------------------------------------------
# Tool: apply_insights (direct write-back + state update plan)
# ------------------------------------------------------------

def tool_apply_insights(params):
    """
    Accepts:
        {
            "reflection": "...",
            "summary": {...},
            "state_node_id": <id>,        # ID of the cognitive_state node in KG
            "state": {...}                # current cognitive_state data
        }

    Returns:
        {
            "write_plan": [ ... ],        # KG write operations
            "updated_state": {...},       # new cognitive_state data
            "message": "..."
        }

    The host is expected to:
        - execute the write_plan (add_node, add_edge, update_state_node)
        - persist updated_state into the cognitive_state node's data
    """

    reflection_text = params.get("reflection", "")
    summary = params.get("summary", {})
    state_node_id = params.get("state_node_id")
    state = params.get("state", {}) or default_cognitive_state()

    active_concepts = summary.get("active_concepts", [])

    write_plan = []

    # 1. Reflection node
    reflection_label = f"Reflection — {datetime.utcnow().isoformat(timespec='seconds')}"
    reflection_node_call = KG_CLIENT.add_node(
        label=reflection_label,
        type_="reflection",
        data={
            "reflection": reflection_text,
            "summary": summary
        }
    )
    write_plan.append(reflection_node_call)

    # 2. Insight node if multiple active concepts
    if len(active_concepts) > 1:
        insight_label = "Concept Cluster: " + ", ".join(active_concepts[:4])
        insight_node_call = KG_CLIENT.add_node(
            label=insight_label,
            type_="insight",
            data={
                "related_concepts": active_concepts
            }
        )
        write_plan.append(insight_node_call)

    # 3. Action node suggesting next steps
    action_label = "Next Step: Enrich graph based on reflection"
    action_node_call = KG_CLIENT.add_node(
        label=action_label,
        type_="action",
        data={
            "source": "cognitive-loop",
            "reflection": reflection_text
        }
    )
    write_plan.append(action_node_call)

    # 4. Update cognitive_state node in the KG
    # We don't know the exact schema of the KG's update_node tool,
    # so we express this as a high-level intention:
    # "knowledge-graph:update_node_data" with state_node_id and updated_state.

    new_state = dict(state)
    new_state["cycle_count"] = state.get("cycle_count", 0) + 1
    new_state["last_cycle_time"] = datetime.utcnow().isoformat(timespec="seconds")
    new_state["last_reflection"] = reflection_text
    new_state["last_summary"] = summary
    new_state["last_active_concepts"] = active_concepts

    update_state_call = {
        "call": "knowledge-graph:update_node_data",
        "arguments": {
            "node_id": state_node_id,
            "data": new_state
        }
    }
    write_plan.append(update_state_call)

    return {
        "write_plan": write_plan,
        "updated_state": new_state,
        "message": "Insights converted into direct write operations and cognitive_state update."
    }

# ------------------------------------------------------------
# Tool: heartbeat (introspection)
# ------------------------------------------------------------

def tool_heartbeat(params):
    """
    A lightweight introspection tool.

    Accepts:
        {
            "state": {...}   # optional cognitive_state data from KG
        }

    Returns:
        - a snapshot of the cognitive loop's last known state
    """

    state = params.get("state", {}) or default_cognitive_state()

    return {
        "status": "ok",
        "state": state,
        "message": (
            "Cognitive Loop v0.5 heartbeat. State is stored in the Knowledge Graph "
            "under a cognitive_state node."
        )
    }

# ------------------------------------------------------------
# Dispatch
# ------------------------------------------------------------

def handle_request(msg):
    method = msg.get("method")
    params = msg.get("params", {})
    req_id = msg.get("id")

    try:
        if method == "initialize":
            send_message({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "cognitive-loop",
                        "version": "0.5.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            })
            return

        if method in ("tools/list", "list_tools"):
            send_message({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "run_cycle",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "mode": { "type": "string" }
                                }
                            }
                        },
                        {
                            "name": "reflect",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "nodes": { "type": "array" },
                                    "edges": { "type": "array" },
                                    "memories": { "type": "array" },
                                    "state": { "type": "object" }
                                }
                            }
                        },
                        {
                            "name": "apply_insights",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "reflection": { "type": "string" },
                                    "summary": { "type": "object" },
                                    "state_node_id": { "type": "integer" },
                                    "state": { "type": "object" }
                                },
                                "required": ["reflection", "summary", "state_node_id"]
                            }
                        },
                        {
                            "name": "heartbeat",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "state": { "type": "object" }
                                }
                            }
                        }
                    ]
                }
            })
            return

        if method in ("tools/call", "call_tool"):
            tool = params.get("name")
            args = params.get("arguments", {})

            if tool == "run_cycle":
                result = tool_run_cycle(args)
            elif tool == "reflect":
                result = tool_reflect(args)
            elif tool == "apply_insights":
                result = tool_apply_insights(args)
            elif tool == "heartbeat":
                result = tool_heartbeat(args)
            else:
                raise ValueError(f"Unknown tool: {tool}")

            send_message({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            })
            return

        send_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}"
            }
        })

    except Exception as e:
        send_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        })

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------

def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        handle_request(msg)

if __name__ == "__main__":
    main()