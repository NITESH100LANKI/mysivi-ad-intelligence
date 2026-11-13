import json
from pathlib import Path
import pytest

WORKFLOW_V3_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v3.json")


def load_v3_workflow():
    assert WORKFLOW_V3_FILE.exists(), f"Workflow file not found: {WORKFLOW_V3_FILE}"
    with open(WORKFLOW_V3_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_v3_nodes_structure():
    wf = load_v3_workflow()
    nodes = wf.get("nodes", [])
    assert len(nodes) == 18, f"Expected 18 nodes, got {len(nodes)}"

    node_ids = set()
    node_names = set()
    for n in nodes:
        assert "id" in n and len(n["id"]) > 0, f"Node missing id: {n}"
        assert "name" in n and len(n["name"]) > 0, f"Node missing name: {n}"
        assert "type" in n and len(n["type"]) > 0, f"Node missing type: {n}"
        assert "position" in n and len(n["position"]) == 2, f"Node missing position: {n}"
        assert n["id"] not in node_ids, f"Duplicate node ID: {n['id']}"
        assert n["name"] not in node_names, f"Duplicate node name: {n['name']}"
        node_ids.add(n["id"])
        node_names.add(n["name"])


def test_v3_connections_validity():
    wf = load_v3_workflow()
    node_names = {n["name"] for n in wf["nodes"]}
    connections = wf.get("connections", {})

    for src_name, channels in connections.items():
        assert src_name in node_names, f"Source node '{src_name}' in connections does not exist in nodes"
        main_outputs = channels.get("main", [])
        assert isinstance(main_outputs, list), f"Expected list of outputs for '{src_name}'"

        for out_idx, target_list in enumerate(main_outputs):
            assert isinstance(target_list, list), f"Target list at out_idx {out_idx} for '{src_name}' must be a list"
            for conn in target_list:
                assert "node" in conn, f"Missing 'node' in connection from '{src_name}'"
                assert "type" in conn and conn["type"] == "main"
                assert "index" in conn and isinstance(conn["index"], int) and conn["index"] >= 0
                target_name = conn["node"]
                assert target_name in node_names, f"Target node '{target_name}' from '{src_name}' does not exist"


def test_v3_execution_mode_router():
    wf = load_v3_workflow()
    connections = wf["connections"]

    router_outputs = connections.get("Execution Mode Router", {}).get("main", [])
    assert len(router_outputs) == 3, f"Execution Mode Router must have 3 output channels, got {len(router_outputs)}"

    c0 = [c["node"] for c in router_outputs[0]]
    assert c0 == ["Apify Start Scraper Run"]

    c1 = [c["node"] for c in router_outputs[1]]
    assert c1 == ["Fetch Apify Dataset Items"]

    c2 = [c["node"] for c in router_outputs[2]]
    assert c2 == ["Load Mock / Fixture Data"]


def test_v3_loop_over_items_connections():
    wf = load_v3_workflow()
    connections = wf["connections"]

    loop_outputs = connections.get("Loop Over Ad Creatives", {}).get("main", [])
    assert len(loop_outputs) == 2, f"Loop Over Ad Creatives must have 2 output channels, got {len(loop_outputs)}"

    # Output 0 (Loop): Has Gemini API Key?
    loop_targets = [c["node"] for c in loop_outputs[0]]
    assert loop_targets == ["Has Gemini API Key?"]

    # Output 1 (Done): Score, Rank & Synthesize Intelligence
    done_targets = [c["node"] for c in loop_outputs[1]]
    assert done_targets == ["Score, Rank & Synthesize Intelligence"]


def test_v3_loop_feedback_connection():
    wf = load_v3_workflow()
    connections = wf["connections"]

    validate_outputs = connections.get("Validate & Structure Ad Analysis", {}).get("main", [])
    assert len(validate_outputs) == 1

    targets = [c["node"] for c in validate_outputs[0]]
    assert "Loop Over Ad Creatives" in targets
    assert "Score, Rank & Synthesize Intelligence" not in targets


def test_v3_graph_cycles_isolation():
    wf = load_v3_workflow()
    connections = wf["connections"]

    adj = {}
    for src, channels in connections.items():
        adj[src] = []
        for target_list in channels.get("main", []):
            for conn in target_list:
                adj[src].append(conn["node"])

    visited = {}
    cycles = []

    def dfs(node, path):
        visited[node] = 1
        for neighbor in adj.get(node, []):
            if neighbor in visited:
                if visited[neighbor] == 1:
                    cycle_start_idx = path.index(neighbor)
                    cycles.append(path[cycle_start_idx:] + [neighbor])
            else:
                dfs(neighbor, path + [neighbor])
        visited[node] = 2

    for node in list(adj.keys()):
        if node not in visited:
            dfs(node, [node])

    assert len(cycles) > 0
    for cycle in cycles:
        assert "Loop Over Ad Creatives" in cycle
        assert "Validate & Structure Ad Analysis" in cycle

