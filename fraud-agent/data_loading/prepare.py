import sys
import logging
import duckdb
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.prepare")

def prepare_data():
    """
    Converts raw CSV files to DuckDB and Parquet (keeping all 393 columns),
    and creates optimized staged views for TigerGraph ingestion.
    """
    db_path = str(config.DUCKDB_PATH)
    parquet_path = str(config.PARQUET_PATH)
    tx_csv = str(config.DATA_DIR / "transactions.csv")
    id_csv = str(config.DATA_DIR / "identity.csv")
    cc_csv = str(config.DATA_DIR / "closed_cases_history.csv")
    cp_csv = str(config.DATA_DIR / "case_pack.csv")

    logger.info(f"Connecting to DuckDB database at {db_path}...")
    con = duckdb.connect(db_path)

    # 1. Ingest transactions.csv keeping all 393 columns
    logger.info("Ingesting transactions.csv into DuckDB table 'transactions_all' (all 393 columns)...")
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS transactions_all AS 
        SELECT * FROM read_csv_auto('{tx_csv}', header=True)
    """)

    # 2. Ingest identity.csv
    logger.info("Ingesting identity.csv into DuckDB table 'identity_all'...")
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS identity_all AS 
        SELECT * FROM read_csv_auto('{id_csv}', header=True)
    """)

    # 3. Ingest closed cases & case pack
    logger.info("Ingesting closed cases and case pack into DuckDB...")
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS closed_cases_raw AS 
        SELECT * FROM read_csv_auto('{cc_csv}', header=True);
        
        CREATE TABLE IF NOT EXISTS case_pack_raw AS 
        SELECT * FROM read_csv_auto('{cp_csv}', header=True);
    """)

    # 4. Export transactions to Parquet for high-speed offline analytical access
    if not Path(parquet_path).exists():
        logger.info(f"Exporting transactions_all to Parquet at {parquet_path}...")
        con.execute(f"COPY transactions_all TO '{parquet_path}' (FORMAT PARQUET)")

    # 5. Create device profile helper column and trimmed views
    logger.info("Creating trimmed graph-ready tables in DuckDB...")
    
    # Pre-aggregate V-features sum to cite V-features honestly as unnamed model signals
    v_cols = [f"V{i}" for i in range(1, 340)]
    v_sum_expr = " + ".join([f"COALESCE(CAST({c} AS DOUBLE), 0)" for c in v_cols])

    con.execute(f"""
        CREATE OR REPLACE VIEW transactions_trimmed AS
        SELECT 
            t.TransactionID as id,
            t.customer_id,
            t.ts,
            CAST(t.TransactionAmt AS DOUBLE) as amount,
            t.ProductCD as product_cd,
            t.channel,
            CAST(t.risk_score AS DOUBLE) as risk_score,
            CAST(t.dist1 AS DOUBLE) as dist1,
            CAST(t.addr1 AS VARCHAR) as addr1,
            CAST(t.addr2 AS VARCHAR) as addr2,
            t.P_emaildomain as p_emaildomain,
            t.R_emaildomain as r_emaildomain,
            t.card4 as card_network,
            t.card6 as card_type,
            i.id_15 as device_new_found,
            i.id_23 as proxy_type,
            CAST(t.C1 AS DOUBLE) as c1,
            CAST(t.C2 AS DOUBLE) as c2,
            CAST(t.C13 AS DOUBLE) as c13,
            CAST(t.D1 AS DOUBLE) as d1,
            CAST(t.D15 AS DOUBLE) as d15,
            t.M4 as m4,
            ({v_sum_expr}) as v_features_sum,
            CASE 
                WHEN i.DeviceInfo IS NOT NULL OR i.id_30 IS NOT NULL OR i.id_31 IS NOT NULL OR i.id_33 IS NOT NULL
                THEN CONCAT_WS(' | ', COALESCE(i.DeviceInfo, 'Unknown Device'), COALESCE(i.id_30, 'Unknown OS'), COALESCE(i.id_31, 'Unknown Browser'), COALESCE(i.id_33, 'Unknown Screen'))
                ELSE NULL
            END as device_profile_id,
            i.DeviceInfo as device_info,
            i.id_30 as os,
            i.id_31 as browser,
            i.id_33 as screen,
            i.DeviceType as device_type
        FROM transactions_all t
        LEFT JOIN identity_all i ON t.TransactionID = i.TransactionID
    """)

    tx_count = con.execute("SELECT count(*) FROM transactions_all").fetchone()[0]
    id_count = con.execute("SELECT count(*) FROM identity_all").fetchone()[0]
    cc_count = con.execute("SELECT count(*) FROM closed_cases_raw").fetchone()[0]
    cp_count = con.execute("SELECT count(*) FROM case_pack_raw").fetchone()[0]

    logger.info(f"Data preparation complete! Summary:")
    logger.info(f"- Transactions: {tx_count:,} rows")
    logger.info(f"- Identity Records: {id_count:,} rows")
    logger.info(f"- Closed Cases: {cc_count:,} rows")
    logger.info(f"- Case Pack Alerts: {cp_count} cases")
    con.close()

if __name__ == "__main__":
    prepare_data()
