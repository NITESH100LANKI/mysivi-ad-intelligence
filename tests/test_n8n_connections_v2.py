import json
from pathlib import Path
import pytest

WORKFLOW_V2_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v2.json")


def load_v2_workflow():
    assert WORKFLOW_V2_FILE.exists(), f"Workflow file not found: {WORKFLOW_V2_FILE}"
    with open(WORKFLOW_V2_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_v2_nodes_structure():
    wf = load_v2_workflow()
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


def test_v2_connections_validity():
    wf = load_v2_workflow()
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


def test_v2_execution_mode_router():
    wf = load_v2_workflow()
    connections = wf["connections"]

    router_outputs = connections.get("Execution Mode Router", {}).get("main", [])
    assert len(router_outputs) == 3, f"Execution Mode Router must have 3 output channels, got {len(router_outputs)}"

    # Channel 0: live -> Apify Start Scraper Run
    c0 = [c["node"] for c in router_outputs[0]]
    assert c0 == ["Apify Start Scraper Run"], f"Channel 0 (live) should route to Apify Start Scraper Run, got {c0}"

    # Channel 1: dataset_replay -> Fetch Apify Dataset Items
    c1 = [c["node"] for c in router_outputs[1]]
    assert c1 == ["Fetch Apify Dataset Items"], f"Channel 1 (replay) should route to Fetch Apify Dataset Items, got {c1}"

    # Channel 2: mock -> Load Mock / Fixture Data
    c2 = [c["node"] for c in router_outputs[2]]
    assert c2 == ["Load Mock / Fixture Data"], f"Channel 2 (mock) should route to Load Mock / Fixture Data, got {c2}"


def test_v2_loop_over_items_connections():
    wf = load_v2_workflow()
    connections = wf["connections"]

    loop_outputs = connections.get("Loop Over Ad Creatives", {}).get("main", [])
    assert len(loop_outputs) == 2, f"Loop Over Ad Creatives must have 2 output channels (loop and done), got {len(loop_outputs)}"

    # Output 0 (Loop): Has Gemini API Key?
    loop_targets = [c["node"] for c in loop_outputs[0]]
    assert loop_targets == ["Has Gemini API Key?"], f"Loop output 0 must connect to 'Has Gemini API Key?', got {loop_targets}"

    # Output 1 (Done): Score, Rank & Synthesize Intelligence
    done_targets = [c["node"] for c in loop_outputs[1]]
    assert done_targets == ["Score, Rank & Synthesize Intelligence"], f"Done output 1 must connect to 'Score, Rank & Synthesize Intelligence', got {done_targets}"


def test_v2_loop_feedback_connection():
    wf = load_v2_workflow()
    connections = wf["connections"]

    validate_outputs = connections.get("Validate & Structure Ad Analysis", {}).get("main", [])
    assert len(validate_outputs) == 1, f"Validate node should have 1 output channel, got {len(validate_outputs)}"

    targets = [c["node"] for c in validate_outputs[0]]
    # MUST connect back to Loop Over Ad Creatives
    assert "Loop Over Ad Creatives" in targets, "Validate node must connect back to 'Loop Over Ad Creatives'"
    # MUST NOT connect directly to Score, Rank & Synthesize Intelligence
    assert "Score, Rank & Synthesize Intelligence" not in targets, (
        "Validate node must NOT connect directly to 'Score, Rank & Synthesize Intelligence'! "
        "Scoring must only be triggered by Loop Over Ad Creatives [Done output]."
    )


def test_v2_graph_cycles_isolation():
    """Verify that the only cycle in the entire directed graph is the intended loop feedback."""
    wf = load_v2_workflow()
    connections = wf["connections"]

    # Build adjacency list
    adj = {}
    for src, channels in connections.items():
        adj[src] = []
        for target_list in channels.get("main", []):
            for conn in target_list:
                adj[src].append(conn["node"])

    # DFS cycle detection
    visited = {}
    cycles = []

    def dfs(node, path):
        visited[node] = 1  # in progress
        for neighbor in adj.get(node, []):
            if neighbor in visited:
                if visited[neighbor] == 1:
                    # Found cycle
                    cycle_start_idx = path.index(neighbor)
                    cycles.append(path[cycle_start_idx:] + [neighbor])
            else:
                dfs(neighbor, path + [neighbor])
        visited[node] = 2  # done

    for node in list(adj.keys()):
        if node not in visited:
            dfs(node, [node])

    # Inspect all cycles found
    assert len(cycles) > 0, "Expected at least one loop cycle"
    for cycle in cycles:
        # Every cycle MUST be the loop cycle between Loop Over Ad Creatives and Validate & Structure Ad Analysis
        assert "Loop Over Ad Creatives" in cycle, f"Unintended cycle detected: {' -> '.join(cycle)}"
        assert "Validate & Structure Ad Analysis" in cycle, f"Unintended cycle detected: {' -> '.join(cycle)}"


def test_v2_fixture_data_contains_all_4_ads():
    """Verify Load Mock / Fixture Data node contains all 4 verified unique advertisements."""
    wf = load_v2_workflow()
    fixture_node = [n for n in wf["nodes"] if n["name"] == "Load Mock / Fixture Data"][0]
    js = fixture_node["parameters"]["jsCode"]

    # Must contain all 4 ad IDs
    assert "946551737840774" in js, "Hindi ad missing from fixture node"
    assert "1843111363320189" in js, "Ad-002 placeholder ad missing from fixture node"
    assert "2966208700429750" in js, "Marathi ad missing from fixture node"
    assert "2823814924671305" in js, "Bengali ad missing from fixture node"

