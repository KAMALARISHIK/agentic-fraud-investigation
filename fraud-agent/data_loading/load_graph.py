import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
import duckdb
from tg_client import TigerGraphManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.load_graph")

BATCH_SIZE = 1000

def batch_upsert_edges(conn, source_type: str, edge_type: str, target_type: str, edge_list: List[Tuple[str, str]]):
    """Upserts edges in high-speed batches."""
    for i in range(0, len(edge_list), BATCH_SIZE):
        chunk = edge_list[i:i+BATCH_SIZE]
        # Format for pyTigerGraph upsertEdges: [(source_id, target_id, attributes), ...]
        formatted = [(src, tgt, {}) for src, tgt in chunk]
        try:
            conn.upsertEdges(source_type, edge_type, target_type, formatted)
        except Exception as e:
            logger.warning(f"Error upserting edge batch {edge_type}: {e}")

def load_graph():
    """
    Idempotently loads the fraud investigation graph into TigerGraph.
    Focuses on case pack entities, historical closed cases, and connected transaction neighborhoods.
    """
    manager = TigerGraphManager()
    if not manager.is_connected():
        logger.error("TigerGraph is not connected. Aborting graph load.")
        return False

    conn = manager.conn
    con = duckdb.connect(str(config.DUCKDB_PATH))

    # 1. Identify Target Focus Customers & Cards
    logger.info("Extracting core customers and cards from case_pack and closed_cases...")
    con.execute("""
        CREATE OR REPLACE TABLE cp_customers AS
        SELECT DISTINCT customer_id, card_id FROM case_pack_raw;

        CREATE OR REPLACE TABLE cc_customers AS
        SELECT DISTINCT customer_id, card_id FROM closed_cases_raw;

        CREATE OR REPLACE TABLE core_customers AS
        SELECT DISTINCT customer_id FROM cp_customers
        UNION
        SELECT DISTINCT customer_id FROM cc_customers;

        CREATE OR REPLACE TABLE core_cards AS
        SELECT DISTINCT card_id, customer_id FROM cp_customers
        UNION
        SELECT DISTINCT card_id, customer_id FROM cc_customers;
    """)

    # 2. Extract Transactions for Case Pack & Closed Cases Focus
    # Priority: All transactions for case pack customers + all closed case transactions + their immediate history
    con.execute("""
        CREATE OR REPLACE TABLE cc_txns_extracted AS
        SELECT DISTINCT CAST(unnest(string_split(txn_ids, '|')) AS BIGINT) as TransactionID
        FROM closed_cases_raw
        WHERE txn_ids IS NOT NULL;

        CREATE OR REPLACE TABLE selected_transactions AS
        SELECT t.*
        FROM transactions_trimmed t
        WHERE t.customer_id IN (SELECT customer_id FROM cp_customers)
           OR t.id IN (SELECT TransactionID FROM cc_txns_extracted);

        CREATE OR REPLACE TABLE shared_devices AS
        SELECT DISTINCT device_profile_id, device_info, os, browser, screen, device_type
        FROM selected_transactions
        WHERE device_profile_id IS NOT NULL;

        CREATE OR REPLACE TABLE shared_regions AS
        SELECT DISTINCT addr1 as region_code, addr2 as country_code
        FROM selected_transactions
        WHERE addr1 IS NOT NULL;

        CREATE OR REPLACE TABLE shared_emails AS
        SELECT DISTINCT p_emaildomain as domain FROM selected_transactions WHERE p_emaildomain IS NOT NULL
        UNION
        SELECT DISTINCT r_emaildomain as domain FROM selected_transactions WHERE r_emaildomain IS NOT NULL;
    """)

    n_cust = con.execute("SELECT count(*) FROM core_customers").fetchone()[0]
    n_cards = con.execute("SELECT count(*) FROM core_cards").fetchone()[0]
    n_txns = con.execute("SELECT count(*) FROM selected_transactions").fetchone()[0]
    n_dev = con.execute("SELECT count(*) FROM shared_devices").fetchone()[0]
    n_reg = con.execute("SELECT count(*) FROM shared_regions").fetchone()[0]
    n_em = con.execute("SELECT count(*) FROM shared_emails").fetchone()[0]
    n_cc = con.execute("SELECT count(*) FROM closed_cases_raw").fetchone()[0]

    logger.info(f"Target Subgraph Statistics:")
    logger.info(f"- Total Core Customers: {n_cust:,}")
    logger.info(f"- Total Core Cards: {n_cards:,}")
    logger.info(f"- Selected High-Signal Transactions: {n_txns:,}")
    logger.info(f"- Device Profiles: {n_dev:,}")
    logger.info(f"- Billing Regions: {n_reg:,}")
    logger.info(f"- Email Domains: {n_em:,}")
    logger.info(f"- Historical Closed Cases: {n_cc:,}")

    # A. Customers
    logger.info("Loading Customer vertices...")
    customers = con.execute("SELECT customer_id FROM core_customers").fetchall()
    for i in range(0, len(customers), BATCH_SIZE):
        batch = {str(row[0]): {"customer_id": str(row[0])} for row in customers[i:i+BATCH_SIZE]}
        conn.upsertVertices("Customer", batch)

    # B. Cards & OWNS Edges
    logger.info("Loading Card vertices & OWNS edges...")
    cards = con.execute("SELECT DISTINCT card_id, customer_id FROM core_cards").fetchall()
    for i in range(0, len(cards), BATCH_SIZE):
        card_batch = {str(cid): {"card_id": str(cid), "card_type": "credit", "card_network": "visa"} for cid, _ in cards[i:i+BATCH_SIZE]}
        conn.upsertVertices("Card", card_batch)
    
    owns_edges = [(str(cust_id), str(cid)) for cid, cust_id in cards]
    batch_upsert_edges(conn, "Customer", "OWNS", "Card", owns_edges)

    # C. Device Profiles
    logger.info("Loading DeviceProfile vertices...")
    devices = con.execute("SELECT device_profile_id, device_info, os, browser, screen, device_type FROM shared_devices").fetchall()
    for i in range(0, len(devices), BATCH_SIZE):
        batch = {
            str(row[0]): {
                "device_info": str(row[1] or ""),
                "os": str(row[2] or ""),
                "browser": str(row[3] or ""),
                "screen": str(row[4] or ""),
                "device_type": str(row[5] or "")
            }
            for row in devices[i:i+BATCH_SIZE]
        }
        conn.upsertVertices("DeviceProfile", batch)

    # D. Billing Regions & Email Domains
    logger.info("Loading BillingRegion and EmailDomain vertices...")
    regions = con.execute("SELECT region_code, country_code FROM shared_regions").fetchall()
    for i in range(0, len(regions), BATCH_SIZE):
        reg_batch = {str(r[0]): {"region_code": str(r[0]), "country_code": str(r[1] or "")} for r in regions[i:i+BATCH_SIZE]}
        conn.upsertVertices("BillingRegion", reg_batch)

    emails = con.execute("SELECT domain FROM shared_emails").fetchall()
    for i in range(0, len(emails), BATCH_SIZE):
        em_batch = {str(e[0]): {"domain": str(e[0])} for e in emails[i:i+BATCH_SIZE]}
        conn.upsertVertices("EmailDomain", em_batch)

    # E. Closed Cases & Edges
    logger.info("Loading ClosedCase vertices & edges...")
    emb_cache = {}
    if config.EMBEDDINGS_CACHE_PATH.exists():
        with open(config.EMBEDDINGS_CACHE_PATH, "r", encoding="utf-8") as f:
            emb_cache = json.load(f)

    closed_cases = con.execute("""
        SELECT case_id, opened_at, closed_at, outcome, pattern, exposure_usd, n_txns, report_filed, analyst_notes, card_id, txn_ids, connected_card_ids
        FROM closed_cases_raw
    """).fetchall()

    cc_on_card_edges = []
    cc_involves_edges = []

    for i in range(0, len(closed_cases), BATCH_SIZE):
        batch = {}
        for row in closed_cases[i:i+BATCH_SIZE]:
            cid, op_at, cl_at, outcome, pat, exp, n_tx, rep, notes, card_id, txn_ids_str, conn_cards = row
            emb = emb_cache.get(f"closed_case:{cid}", [0.0] * 768)
            batch[str(cid)] = {
                "opened_at": str(op_at),
                "closed_at": str(cl_at or op_at),
                "outcome": str(outcome or ""),
                "pattern": str(pat or ""),
                "exposure_usd": float(exp or 0.0),
                "n_txns": int(n_tx or 1),
                "report_filed": bool(rep == "true" or rep is True),
                "analyst_notes": str(notes or "")[:1000],
                "embedding": emb
            }
            if card_id:
                cc_on_card_edges.append((str(cid), str(card_id)))
            if txn_ids_str:
                for tx_item in str(txn_ids_str).split("|"):
                    if tx_item.strip():
                        cc_involves_edges.append((str(cid), str(tx_item.strip())))

        conn.upsertVertices("ClosedCase", batch)

    batch_upsert_edges(conn, "ClosedCase", "ON_CARD", "Card", cc_on_card_edges)
    batch_upsert_edges(conn, "ClosedCase", "INVOLVES", "Transaction", cc_involves_edges)

    # F. Transactions & Graph Edges
    logger.info("Loading Transactions and relational edges...")
    txns = con.execute("""
        SELECT id, ts, amount, product_cd, channel, risk_score, dist1, addr1, addr2, 
               p_emaildomain, r_emaildomain, device_new_found, proxy_type, 
               c1, c2, c13, d1, d15, m4, v_features_sum, customer_id, device_profile_id
        FROM selected_transactions
        ORDER BY customer_id, ts
    """).fetchall()

    logger.info(f"Uploading {len(txns)} transactions to TigerGraph in batches of {BATCH_SIZE}...")
    for i in range(0, len(txns), BATCH_SIZE):
        chunk = txns[i:i+BATCH_SIZE]
        tx_batch = {}
        made_edges = []
        dev_edges = []
        p_email_edges = []
        r_email_edges = []
        billed_edges = []
        next_edges = []

        prev_cust = None
        prev_tid = None

        for row in chunk:
            tid = str(row[0])
            ts = str(row[1])
            amt = float(row[2] or 0.0)
            pcd = str(row[3] or "")
            chan = str(row[4] or "")
            r_score = float(row[5] or 0.0)
            dist = float(row[6] or 0.0)
            a1 = str(row[7] or "")
            a2 = str(row[8] or "")
            p_em = str(row[9] or "")
            r_em = str(row[10] or "")
            d_new = str(row[11] or "")
            prox = str(row[12] or "")
            c1, c2, c13 = float(row[13] or 0.0), float(row[14] or 0.0), float(row[15] or 0.0)
            d1, d15 = float(row[16] or 0.0), float(row[17] or 0.0)
            m4 = str(row[18] or "")
            v_sum = float(row[19] or 0.0)
            cust_id = str(row[20])
            dev_id = row[21]

            tx_batch[tid] = {
                "ts": ts,
                "amount": amt,
                "product_cd": pcd,
                "channel": chan,
                "risk_score": r_score,
                "dist1": dist,
                "addr1": a1,
                "addr2": a2,
                "p_emaildomain": p_em,
                "r_emaildomain": r_em,
                "device_new_found": d_new,
                "proxy_type": prox,
                "c1": c1,
                "c2": c2,
                "c13": c13,
                "d1": d1,
                "d15": d15,
                "m4": m4,
                "v_features_sum": v_sum
            }

            card_id = f"{cust_id}-K1"
            made_edges.append((card_id, tid))
            if dev_id:
                dev_edges.append((tid, str(dev_id)))
            if p_em:
                p_email_edges.append((tid, str(p_em)))
            if r_em:
                r_email_edges.append((tid, str(r_em)))
            if a1:
                billed_edges.append((tid, str(a1)))
            
            if prev_cust == cust_id and prev_tid:
                next_edges.append((prev_tid, tid))
            prev_cust = cust_id
            prev_tid = tid

        conn.upsertVertices("Transaction", tx_batch)
        batch_upsert_edges(conn, "Card", "MADE", "Transaction", made_edges)
        batch_upsert_edges(conn, "Transaction", "FROM_DEVICE", "DeviceProfile", dev_edges)
        batch_upsert_edges(conn, "Transaction", "PURCHASER_EMAIL", "EmailDomain", p_email_edges)
        batch_upsert_edges(conn, "Transaction", "RECIPIENT_EMAIL", "EmailDomain", r_email_edges)
        batch_upsert_edges(conn, "Transaction", "BILLED_IN", "BillingRegion", billed_edges)
        batch_upsert_edges(conn, "Transaction", "NEXT", "Transaction", next_edges)

        logger.info(f"Loaded {min(i+BATCH_SIZE, len(txns))}/{len(txns)} transactions...")

    logger.info("Graph loading successfully completed!")
    try:
        v_counts = conn.getVertexCount("*")
        logger.info(f"TigerGraph Total Vertex Counts: {v_counts}")
    except Exception as e:
        logger.warning(f"Could not fetch vertex counts: {e}")

    con.close()
    return True

if __name__ == "__main__":
    load_graph()
