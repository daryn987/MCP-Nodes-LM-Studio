#!/usr/bin/env python3
import json
import sys
import sqlite3
from datetime import datetime

DB_PATH = "knowledge_graph.db"

# ------------------------------------------------------------
# DB setup
# ------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            type TEXT,
            data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            relation TEXT,
            data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_id) REFERENCES nodes(id),
            FOREIGN KEY(target_id) REFERENCES nodes(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

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
# Tools
# ------------------------------------------------------------

def tool_add_node(params):
    label = params.get("label")
    type_ = params.get("type")
    data = params.get("data", {})

    if not label:
        raise ValueError("label is required")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO nodes (label, type, data) VALUES (?, ?, ?)",
        (label, type_, json.dumps(data))
    )
    conn.commit()
    node_id = cur.lastrowid
    conn.close()

    return {
        "node_id": node_id,
        "label": label,
        "type": type_,
        "data": data
    }

def tool_add_edge(params):
    source_id = params.get("source_id")
    target_id = params.get("target_id")
    relation = params.get("relation")
    data = params.get("data", {})

    if source_id is None or target_id is None:
        raise ValueError("source_id and target_id are required")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO edges (source_id, target_id, relation, data) VALUES (?, ?, ?, ?)",
        (source_id, target_id, relation, json.dumps(data))
    )
    conn.commit()
    edge_id = cur.lastrowid
    conn.close()

    return {
        "edge_id": edge_id,
        "source_id": source_id,
        "target_id": target_id,
        "relation": relation,
        "data": data
    }

def tool_list_recent_nodes(params):
    limit = params.get("limit", 20)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, label, type, data, created_at FROM nodes ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()

    nodes = []
    for row in rows:
        data = json.loads(row["data"]) if row["data"] else {}
        nodes.append({
            "id": row["id"],
            "label": row["label"],
            "type": row["type"],
            "data": data,
            "created_at": row["created_at"]
        })

    return {"nodes": nodes}

def tool_list_recent_edges(params):
    limit = params.get("limit", 20)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, source_id, target_id, relation, data, created_at FROM edges ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()

    edges = []
    for row in rows:
        data = json.loads(row["data"]) if row["data"] else {}
        edges.append({
            "id": row["id"],
            "source_id": row["source_id"],
            "target_id": row["target_id"],
            "relation": row["relation"],
            "data": data,
            "created_at": row["created_at"]
        })

    return {"edges": edges}

def tool_find_or_create_state_node(params):
    label = params.get("label")
    type_ = params.get("type")

    if not label or not type_:
        raise ValueError("label and type are required")

    conn = get_db()
    cur = conn.cursor()

    # 1. Try to find existing cognitive_state node
    cur.execute(
        "SELECT id, label, type, data FROM nodes WHERE type = ? LIMIT 1",
        (type_,)
    )
    row = cur.fetchone()

    if row:
        node_id = row["id"]
        label = row["label"]
        type_ = row["type"]
        data_json = row["data"]
        data = json.loads(data_json) if data_json else {}
        conn.close()
        return {
            "node_id": node_id,
            "label": label,
            "type": type_,
            "data": data,
            "created": False
        }

    # 2. Create new cognitive_state node
    default_state = {
        "cycle_count": 0,
        "last_cycle_time": None,
        "last_mode": "normal",
        "last_reflection": None,
        "last_summary": None,
        "last_written_nodes": [],
        "last_written_edges": [],
        "last_active_concepts": [],
        "last_memory_snapshot": []
    }

    cur.execute(
        "INSERT INTO nodes (label, type, data) VALUES (?, ?, ?)",
        (label, type_, json.dumps(default_state))
    )
    conn.commit()
    node_id = cur.lastrowid
    conn.close()

    return {
        "node_id": node_id,
        "label": label,
        "type": type_,
        "data": default_state,
        "created": True
    }

def tool_update_node_data(params):
    node_id = params.get("node_id")
    data = params.get("data")

    if node_id is None:
        raise ValueError("node_id is required")
    if data is None:
        raise ValueError("data is required")

    conn = get_db()
    cur = conn.cursor()

    # Ensure node exists
    cur.execute("SELECT id FROM nodes WHERE id = ?", (node_id,))
    if cur.fetchone() is None:
        conn.close()
        raise ValueError(f"Node {node_id} does not exist")

    # Update data
    cur.execute(
        "UPDATE nodes SET data = ? WHERE id = ?",
        (json.dumps(data), node_id)
    )
    conn.commit()
    conn.close()

    return {
        "node_id": node_id,
        "updated": True,
        "data": data
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
                        "name": "knowledge-graph",
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
                            "name": "add_node",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "label": { "type": "string" },
                                    "type": { "type": "string" },
                                    "data": { "type": "object" }
                                },
                                "required": ["label"]
                            }
                        },
                        {
                            "name": "add_edge",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "source_id": { "type": "integer" },
                                    "target_id": { "type": "integer" },
                                    "relation": { "type": "string" },
                                    "data": { "type": "object" }
                                },
                                "required": ["source_id", "target_id"]
                            }
                        },
                        {
                            "name": "list_recent_nodes",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": { "type": "integer" }
                                }
                            }
                        },
                        {
                            "name": "list_recent_edges",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": { "type": "integer" }
                                }
                            }
                        },
                        {
                            "name": "find_or_create_state_node",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "label": { "type": "string" },
                                    "type": { "type": "string" }
                                },
                                "required": ["label", "type"]
                            }
                        },
                        {
                            "name": "update_node_data",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "node_id": { "type": "integer" },
                                    "data": { "type": "object" }
                                },
                                "required": ["node_id", "data"]
                            }
                        }
                    ]
                }
            })
            return

        if method in ("tools/call", "call_tool"):
            tool = params.get("name")
            args = params.get("arguments", {})

            if tool == "add_node":
                result = tool_add_node(args)
            elif tool == "add_edge":
                result = tool_add_edge(args)
            elif tool == "list_recent_nodes":
                result = tool_list_recent_nodes(args)
            elif tool == "list_recent_edges":
                result = tool_list_recent_edges(args)
            elif tool == "find_or_create_state_node":
                result = tool_find_or_create_state_node(args)
            elif tool == "update_node_data":
                result = tool_update_node_data(args)
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