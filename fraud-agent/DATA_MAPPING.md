# Dataset & Card ID Mapping Documentation

## 1. Overview & Key Findings

Analysis of all 590,742 transactions, 5,565 closed cases, and 20 exam cases confirms:

1. **Customer ID (`customer_id`) ↔ `card1` Relationship**:
   - `customer_id` (e.g. `C01234`, `C12382`) has an exact 1-to-1 bijective mapping with `card1`.
   - Every `customer_id` corresponds to a unique `card1` issuer value, and every `card1` corresponds to a single `customer_id`.

2. **Card ID (`card_id`) Structure**:
   - Card identifiers follow the deterministic format `<customer_id>-K<N>` (e.g. `C12382-K1`, `C08623-K2`).
   - Suffix `-K1`, `-K2`, `-K3` identifies specific card payment instruments held by the customer.
   - Distinct cards for the same customer are differentiated by their card attributes:
     - `card4`: Card Network (`visa`, `mastercard`, `american express`, `discover`)
     - `card6`: Card Type (`credit`, `debit`)
     - `card2`, `card3`, `card5`: Numerical issuer/product parameters.

3. **Transaction Association**:
   - Every flagged transaction in `case_pack.csv` and `closed_cases_history.csv` links to `transactions.csv` on `TransactionID`.
   - The transaction row contains the full set of attributes: `customer_id`, `ts`, `TransactionAmt`, `ProductCD`, `channel`, `risk_score`, `card1..card6`, `addr1`, `addr2`, and `dist1`.
   - Online transactions (`channel == 'online'`) join with `identity.csv` on `TransactionID` to provide device parameters: `DeviceInfo`, `id_15` (New/Found), `id_23` (proxy type), `id_30` (OS), `id_31` (browser), and `id_33` (screen resolution).

## 2. Graph Entity Mapping

- **Customer Vertex (`Customer`)**: `id = customer_id`
- **Card Vertex (`Card`)**: `id = card_id` (or derived `<customer_id>-K1` when unassigned)
- **Transaction Vertex (`Transaction`)**: `id = TransactionID`
- **DeviceProfile Vertex (`DeviceProfile`)**: `id = "<DeviceInfo> | <OS> | <browser> | <screen>"`
- **EmailDomain Vertex (`EmailDomain`)**: `id = P_emaildomain` / `R_emaildomain`
- **BillingRegion Vertex (`BillingRegion`)**: `id = addr1` (string code)
- **ClosedCase Vertex (`ClosedCase`)**: `id = case_id` (from `closed_cases_history.csv`)
- **Case Vertex (`Case`)**: `id = case_id` (for newly created/investigated cases)
