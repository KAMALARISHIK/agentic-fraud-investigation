import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.tools import tools

def test_card_window_query():
    # Card from Case Pack HHG-001
    card_id = "C12382-K1"
    res = tools.card_window(card_id, "2016-12-01 00:00:00", "2016-12-31 23:59:59")
    assert isinstance(res, list)
    assert len(res) > 0
    assert "amount" in res[0]
    assert "ts" in res[0]

def test_customer_baseline_query():
    customer_id = "C12382"
    baseline = tools.customer_baseline(customer_id)
    assert isinstance(baseline, dict)
    assert baseline["total_txns"] > 0
    assert baseline["avg_amount"] > 0

def test_small_auth_sequence_card_testing():
    # Case HHG-017 / Card Testing
    card_id = "C04570-K1"
    res = tools.small_auth_sequence(card_id, "2016-11-12 00:46:24", window_hours=24)
    assert isinstance(res, dict)
    assert "is_card_testing" in res
    assert "small_auth_count" in res

def test_new_device_proxy_query():
    txn_id = "3450629"
    res = tools.new_device_proxy(txn_id)
    assert isinstance(res, dict)
    assert "is_new_device" in res
    assert "is_proxy" in res

def test_out_of_region_query():
    card_id = "C12382-K1"
    txn_id = "3514030"
    res = tools.out_of_region(card_id, txn_id)
    assert isinstance(res, dict)
    assert "is_out_of_region" in res
    assert "is_clone_suspected" in res

def test_recurring_charge_query():
    card_id = "C08623-K2"
    res = tools.recurring_charge(card_id, 49.00)
    assert isinstance(res, dict)
    assert "is_recurring_charge" in res

def test_similar_closed_cases():
    res = tools.similar_closed_cases(pattern_hint="card_testing", top_k=3)
    assert isinstance(res, list)
    assert len(res) > 0
    assert "case_id" in res[0]

def test_card_neighborhood_graph():
    card_id = "C12382-K1"
    graph_data = tools.card_neighborhood_graph(card_id)
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["edges"]) > 0
