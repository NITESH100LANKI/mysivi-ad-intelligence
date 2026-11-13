import json
from pathlib import Path
import pytest

WORKFLOW_V4_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v4.json")


def load_v4_workflow():
    assert WORKFLOW_V4_FILE.exists(), f"Workflow file not found: {WORKFLOW_V4_FILE}"
    with open(WORKFLOW_V4_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_v4_nodes_structure():
    wf = load_v4_workflow()
    nodes = wf.get("nodes", [])
    assert len(nodes) == 20, f"Expected 20 nodes, got {len(nodes)}"

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

    # Specific required nodes in v4
    assert "Aggregate Validated Advertisements" in node_names
    assert "Validate Scoring Input" in node_names
    assert "Score, Rank & Synthesize Intelligence" in node_names


def test_v4_connections_validity():
    wf = load_v4_workflow()
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


def test_v4_loop_over_items_connections():
    wf = load_v4_workflow()
    connections = wf["connections"]

    loop_outputs = connections.get("Loop Over Ad Creatives", {}).get("main", [])
    assert len(loop_outputs) == 2, f"Loop Over Ad Creatives must have 2 output channels, got {len(loop_outputs)}"

    # Output 0 (Loop): Has Gemini API Key?
    loop_targets = [c["node"] for c in loop_outputs[0]]
    assert loop_targets == ["Has Gemini API Key?"], f"Output 0 must connect to 'Has Gemini API Key?', got {loop_targets}"

    # Output 1 (Done): Aggregate Validated Advertisements
    done_targets = [c["node"] for c in loop_outputs[1]]
    assert done_targets == ["Aggregate Validated Advertisements"], f"Output 1 (Done) must connect to 'Aggregate Validated Advertisements', got {done_targets}"


def test_v4_pipeline_downstream_sequence():
    wf = load_v4_workflow()
    connections = wf["connections"]

    # 1. Aggregate -> Validate Scoring Input
    agg_targets = [c["node"] for c in connections.get("Aggregate Validated Advertisements", {}).get("main", [[]])[0]]
    assert agg_targets == ["Validate Scoring Input"]

    # 2. Validate Scoring Input -> Score, Rank & Synthesize Intelligence
    val_targets = [c["node"] for c in connections.get("Validate Scoring Input", {}).get("main", [[]])[0]]
    assert val_targets == ["Score, Rank & Synthesize Intelligence"]

    # 3. Score -> Trigger PDF Report Generation
    score_targets = [c["node"] for c in connections.get("Score, Rank & Synthesize Intelligence", {}).get("main", [[]])[0]]
    assert score_targets == ["Trigger PDF Report Generation"]

    # 4. Trigger PDF -> Final Execution Summary
    pdf_targets = [c["node"] for c in connections.get("Trigger PDF Report Generation", {}).get("main", [[]])[0]]
    assert pdf_targets == ["Final Execution Summary"]


def test_v4_graph_cycles_isolation():
    """Verify that the only cycle in the entire directed graph is the loop feedback."""
    wf = load_v4_workflow()
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

