import pytest
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_card_id_format_and_customer_prefix():
    """Verify that all card_id values in case_pack and closed_cases follow <customer_id>-K<N>."""
    con = duckdb.connect()
    
    # Check case_pack.csv
    cp_path = str(BASE_DIR / "case_pack.csv")
    cp_res = con.execute(f"""
        SELECT case_id, customer_id, card_id 
        FROM '{cp_path}'
        WHERE split_part(card_id, '-', 1) != customer_id
           OR NOT regexp_matches(card_id, '^C[0-9]+-K[0-9]+$')
    """).fetchall()
    assert len(cp_res) == 0, f"Found invalid card_id formatting in case_pack.csv: {cp_res}"

    # Check closed_cases_history.csv
    cc_path = str(BASE_DIR / "closed_cases_history.csv")
    cc_res = con.execute(f"""
        SELECT case_id, customer_id, card_id 
        FROM '{cc_path}'
        WHERE split_part(card_id, '-', 1) != customer_id
           OR NOT regexp_matches(card_id, '^C[0-9]+-K[0-9]+$')
    """).fetchall()
    assert len(cc_res) == 0, f"Found invalid card_id formatting in closed_cases_history.csv: {cc_res}"

def test_customer_id_bijective_to_card1():
    """Verify that customer_id is 1-to-1 with card1 in transactions.csv."""
    con = duckdb.connect()
    tx_path = str(BASE_DIR / "transactions.csv")
    
    # Check sample/full of transactions
    mismatches = con.execute(f"""
        SELECT customer_id, count(distinct card1) as n_card1
        FROM '{tx_path}'
        GROUP BY customer_id
        HAVING n_card1 > 1
    """).fetchall()
    assert len(mismatches) == 0, f"Found customer_id with multiple card1: {mismatches}"

def test_flagged_transactions_exist_in_transactions():
    """Verify that all flagged transactions in case_pack exist in transactions.csv."""
    con = duckdb.connect()
    cp_path = str(BASE_DIR / "case_pack.csv")
    tx_path = str(BASE_DIR / "transactions.csv")
    
    missing = con.execute(f"""
        SELECT cp.case_id, cp.flagged_txn_id
        FROM '{cp_path}' cp
        LEFT JOIN '{tx_path}' t ON cp.flagged_txn_id = t.TransactionID
        WHERE t.TransactionID IS NULL
    """).fetchall()
    assert len(missing) == 0, f"Flagged transactions not found in transactions.csv: {missing}"
