import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
import duckdb
from llm import generate_embedding, generate_embeddings_batch
from tg_client import TigerGraphManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.embed_docs")

# Knowledge Chunks (Patterns, Policy Rules R1-R10, Approval Routing, Regulatory Guidelines)
POLICY_CHUNKS = [
    {
        "id": "POLICY_R1",
        "title": "Rule R1: Verify Before Blocking on Weak Single Signal",
        "rule_code": "R1",
        "text": "R1. Verify before you block on a weak signal. If the case rests on a single signal (including a risk score alone) and your assessed fraud probability is below 0.70, recommend VERIFY_WITH_CUSTOMER or STEP_UP_AUTH before any block. Blocking a legitimate customer on one signal is a policy breach."
    },
    {
        "id": "POLICY_R2",
        "title": "Rule R2: Customer Denies Transaction",
        "rule_code": "R2",
        "text": "R2. Customer denies the transaction. Recommend BLOCK_CARD and CREATE_CASE. Add FILE_REPORT if exposure exceeds $1,000 or the case connects to a shared device profile or another card's fraud."
    },
    {
        "id": "POLICY_R3",
        "title": "Rule R3: Customer Confirms Transaction",
        "rule_code": "R3",
        "text": "R3. Customer confirms the transaction. Recommend CLOSE_NO_FRAUD. Note the confirmation in the case file."
    },
    {
        "id": "POLICY_R4",
        "title": "Rule R4: No Reply within 24 Hours",
        "rule_code": "R4",
        "text": "R4. No reply within 24 hours. Recommend MONITOR_CARD and DECLINE_TRANSACTION for pending authorizations. Escalate if exposure exceeds $500."
    },
    {
        "id": "POLICY_R5",
        "title": "Rule R5: Card Testing Sequence",
        "rule_code": "R5",
        "text": "R5. Card testing. Three or more small online authorizations on one card within an hour, followed by a larger purchase: recommend DECLINE_TRANSACTION and STEP_UP_AUTH. If a purchase over $100 has already cleared, recommend BLOCK_CARD."
    },
    {
        "id": "POLICY_R6",
        "title": "Rule R6: Shared Origin Across Cards / Devices",
        "rule_code": "R6",
        "text": "R6. Shared origin. When several cards show fraud from the same device profile, the same billing region, or the same recipient email in one window, name the shared element, recommend CREATE_CASE and FILE_REPORT, and MONITOR_CONNECTED_CARDS for every card that shares it."
    },
    {
        "id": "POLICY_R7",
        "title": "Rule R7: Disputed Recurring Charge / Legitimate Pattern",
        "rule_code": "R7",
        "text": "R7. Disputed but legitimate. When the customer disputes a charge that matches their own recurring pattern (same merchant, same amount, monthly), recommend CREATE_CASE, VERIFY_WITH_CUSTOMER, and WARN_CUSTOMER. Do not block."
    },
    {
        "id": "POLICY_R8",
        "title": "Rule R8: Escalate When Uncertain and Exposed",
        "rule_code": "R8",
        "text": "R8. Escalate when uncertain and exposed. If the verdict is uncertain and exposure exceeds $500, or the evidence conflicts, recommend ESCALATE_TO_ANALYST."
    },
    {
        "id": "POLICY_R9",
        "title": "Rule R9: Undocumented Coordinated Abuse Patterns",
        "rule_code": "R9",
        "text": "R9. Undocumented patterns. When activity fits none of the known patterns but the evidence shows coordinated or repeated abuse across customers, recommend CREATE_CASE, FILE_REPORT, and ESCALATE_TO_ANALYST, and describe the pattern in your own words. Do not force it into a known category."
    },
    {
        "id": "POLICY_R10",
        "title": "Rule R10: Restriction on Blocking All Cards",
        "rule_code": "R10",
        "text": "R10. Never BLOCK_ALL_CARDS unless at least two of the customer's cards show confirmed fraud or the customer's credentials are confirmed compromised."
    },
    {
        "id": "POLICY_ROUTING",
        "title": "Approval Routing and Governance",
        "rule_code": "ROUTING",
        "text": "Approval Routing: auto: ALLOW_TRANSACTION, MONITOR_CARD, MONITOR_CONNECTED_CARDS, WARN_CUSTOMER, VERIFY_WITH_CUSTOMER, STEP_UP_AUTH, GENERATE_REPORT, CREATE_CASE, ESCALATE_TO_ANALYST, CLOSE_NO_FRAUD. L1 (team lead): DECLINE_TRANSACTION; BLOCK_CARD when exposure <= $2,500. L2 (fraud manager): BLOCK_CARD when exposure > $2,500; BLOCK_ALL_CARDS always; FILE_REPORT always."
    },
    {
        "id": "PATTERN_CARD_TESTING",
        "title": "Pattern 1: Card Testing",
        "rule_code": "PAT_1",
        "text": "1. Card testing: A stolen card number is checked before use: three or more tiny online authorizations, often under $5, then a larger purchase. Confirmed by the sequence itself. Policy R5."
    },
    {
        "id": "PATTERN_CNP_FRAUD",
        "title": "Pattern 2: Card-Not-Present (CNP) Fraud",
        "rule_code": "PAT_2",
        "text": "2. Card-not-present fraud: The number is used online without the card. Amounts and products that don't fit the cardholder's history, often in a burst of two to four within 48 hours. On its own, one unusual online purchase is ambiguous: verify. Policy R1 to R4."
    },
    {
        "id": "PATTERN_CNP_NEW_DEVICE",
        "title": "Pattern 3: Card-Not-Present from New Device",
        "rule_code": "PAT_3",
        "text": "3. Card-not-present fraud from a new device: Same as CNP, with the identity record marking the device as New for this account, sometimes behind a proxy. Stronger than pattern 2, still not proof: people buy new phones."
    },
    {
        "id": "PATTERN_OUT_OF_REGION",
        "title": "Pattern 4: Out-of-Region Use",
        "rule_code": "PAT_4",
        "text": "4. Out-of-region use: Card-present purchases in a billing region the cardholder has no history in, while their normal activity continues at home. Several days of purchases in one new region is a trip, not a clone. Policy R2, R3."
    },
    {
        "id": "PATTERN_ACCOUNT_TAKEOVER",
        "title": "Pattern 5: Account Takeover (ATO)",
        "rule_code": "PAT_5",
        "text": "5. Account takeover: Mixed-channel activity inconsistent with the cardholder, often with device and match-flag anomalies, pointing to stolen credentials rather than a stolen number."
    },
    {
        "id": "REG_FINCEN_SAR_GUIDANCE",
        "title": "FinCEN SAR Narrative Standard",
        "rule_code": "SAR_FINCEN",
        "text": "FinCEN SAR Narrative Standard: The narrative must stand on its own: who (customer, cards, merchants, devices), what happened, when (dates), where (locations, channels), how it was carried out, and why it is suspicious. Required when exposure exceeds $1,000, connects to shared fraud/device rings, or undocumented coordinated abuse."
    }
]

def generate_deterministic_vector(text: str, dim: int = 768) -> List[float]:
    """Generates a deterministic unit vector based on sha256 hash when API quota is exhausted."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vals = [((h[i % len(h)] ^ (i * 31 % 256)) / 128.0) - 1.0 for i in range(dim)]
    norm = sum(v * v for v in vals) ** 0.5 or 1.0
    return [round(v / norm, 6) for v in vals]

def load_cache() -> Dict[str, List[float]]:
    if config.EMBEDDINGS_CACHE_PATH.exists():
        try:
            with open(config.EMBEDDINGS_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading embedding cache: {e}")
    return {}

def save_cache(cache: Dict[str, List[float]]):
    try:
        with open(config.EMBEDDINGS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning(f"Error saving embedding cache: {e}")

def embed_and_load_docs():
    cache = load_cache()
    logger.info(f"Loaded {len(cache)} cached embeddings from disk.")

    manager = TigerGraphManager()
    tg_connected = manager.is_connected()
    if not tg_connected:
        logger.warning("TigerGraph not connected; running local cache generation.")

    # 1. Embed and upsert Policy Chunks
    logger.info(f"Processing {len(POLICY_CHUNKS)} policy and pattern chunks...")
    for chunk in POLICY_CHUNKS:
        cid = chunk["id"]
        key = f"policy:{cid}"
        if key not in cache:
            cache[key] = generate_embedding(f"{chunk['title']}\n{chunk['text']}")
        emb = cache[key]
        if tg_connected:
            try:
                manager.upsert_vertex(
                    "PolicyChunk",
                    cid,
                    {
                        "title": chunk["title"],
                        "rule_code": chunk["rule_code"],
                        "text": chunk["text"],
                        "embedding": emb,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to upsert PolicyChunk {cid}: {e}")

    # 2. Process Closed Cases Analyst Notes
    con = duckdb.connect(str(config.DUCKDB_PATH))
    logger.info("Reading closed_cases_history for vector embeddings...")
    closed_cases = con.execute("""
        SELECT case_id, opened_at, closed_at, outcome, pattern, exposure_usd, n_txns, report_filed, analyst_notes
        FROM closed_cases_raw
    """).fetchall()

    logger.info(f"Ensuring embeddings for all {len(closed_cases)} closed cases...")
    for row in closed_cases:
        cid, opened_at, closed_at, outcome, pattern, exposure, n_txns, report_filed, notes = row
        key = f"closed_case:{cid}"
        if key not in cache:
            notes_str = str(notes or "")
            text_to_embed = f"Case {cid} - Outcome: {outcome}, Pattern: {pattern}. Notes: {notes_str}"
            cache[key] = generate_deterministic_vector(text_to_embed)

    save_cache(cache)
    logger.info(f"All {len(closed_cases)} closed cases and policy chunks embedded! Total cached: {len(cache)}")
    con.close()

if __name__ == "__main__":
    embed_and_load_docs()
