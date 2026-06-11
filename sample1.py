import streamlit as st
import pandas as pd
import json
from pathlib import Path
from sqlalchemy import create_engine, text
import datetime

# ---------------------------
# Paths & DB connection setup
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH  = BASE_DIR / "banksight.db"

def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

# ---------------------------
# Utilities: JSON reader
# ---------------------------
def read_json_file(path: Path) -> pd.DataFrame:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.json_normalize(data)
    except json.JSONDecodeError:
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        continue
        return pd.json_normalize(records)

# ---------------------------
# Auto-create DB if missing
# ---------------------------
def create_database_from_data():
    if DB_PATH.exists():
        return False

    if not DATA_DIR.exists():
        st.warning(f"Data folder not found at {DATA_DIR}. Place your CSV/JSON files there.")
        return False

    engine = get_engine()

    csv_files  = {
        "customers.csv": "customers",
        "accounts.csv": "accounts",
        "transactions.csv": "transactions"
    }
    json_files = {
        "branches.json": "branches",
        "loans.json": "loans",
        "credit_cards.json": "credit_cards",
        "support_tickets.json": "support_tickets"
    }

    for fname, table in csv_files.items():
        p = DATA_DIR / fname
        if p.exists():
            try:
                df = pd.read_csv(p)
                df.columns = [c.strip() for c in df.columns]
                df.to_sql(table, engine, index=False, if_exists="replace")
            except Exception as e:
                st.error(f"Failed to load {fname}: {e}")
        else:
            st.warning(f"{fname} not found in data/ folder.")

    for fname, table in json_files.items():
        p = DATA_DIR / fname
        if p.exists():
            try:
                df = read_json_file(p)
                df.columns = [c.strip() for c in df.columns]
                df.to_sql(table, engine, index=False, if_exists="replace")
            except Exception as e:
                st.error(f"Failed to load {fname}: {e}")
        else:
            st.warning(f"{fname} not found in data/ folder.")

    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id);"))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_txn_customer ON transactions(customer_id);"))
        except Exception:
            pass

    st.success(f"Database created at {DB_PATH}")
    return True

# ---------------------------
# Cached DB reads
# ---------------------------
@st.cache_data(show_spinner=False)
def read_table(table_name: str, limit: int = 1000) -> pd.DataFrame:
    engine = get_engine()
    try:
        return pd.read_sql_query(text(f"SELECT * FROM {table_name} LIMIT {limit}"), engine)
    except Exception:
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def read_sql_query(query: str) -> pd.DataFrame:
    engine = get_engine()
    try:
        return pd.read_sql_query(text(query), engine)
    except Exception:
        return pd.DataFrame()

# ---------------------------
# Helper: get all table names
# ---------------------------
def get_tables():
    engine = get_engine()
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            return [r[0] for r in res.fetchall()]
    except Exception:
        return []

# ---------------------------
# CRUD helpers
# ---------------------------
def insert_record(table: str, record: dict):
    engine = get_engine()
    cols = ", ".join(record.keys())
    vals = ", ".join([f":{k}" for k in record.keys()])
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"), record)
    read_table.clear()
    read_sql_query.clear()

def update_record(table: str, pk_col: str, pk_val, updates: dict):
    engine = get_engine()
    set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
    params = updates.copy()
    params["pk_val"] = pk_val
    with engine.begin() as conn:
        conn.execute(text(f"UPDATE {table} SET {set_clause} WHERE {pk_col} = :pk_val"), params)
    read_table.clear()
    read_sql_query.clear()

def delete_record(table: str, pk_col: str, pk_val):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table} WHERE {pk_col} = :v"), {"v": pk_val})
    read_table.clear()
    read_sql_query.clear()

# ---------------------------
# Analytical SQL queries
# ---------------------------
SQL_QUERIES = {
    "Q1: Customers per city & avg balance":
        """SELECT c.city, COUNT(*) AS total_customers, ROUND(AVG(a.account_balance),2) AS avg_balance
           FROM customers c JOIN accounts a ON c.customer_id = a.customer_id
           GROUP BY c.city ORDER BY avg_balance DESC;""",

    "Q2: Account type holding highest total balance":
        """SELECT c.account_type, SUM(a.account_balance) AS total_balance
           FROM customers c JOIN accounts a ON c.customer_id = a.customer_id
           GROUP BY c.account_type ORDER BY total_balance DESC;""",

    "Q3: Top 10 customers by total balance":
        """SELECT c.customer_id, c.name, c.city, a.account_balance
           FROM customers c JOIN accounts a ON c.customer_id = a.customer_id
           ORDER BY a.account_balance DESC LIMIT 10;""",

    "Q4: Customers in 2023 with balance > 100000":
        """SELECT c.customer_id, c.name, c.city, c.join_date, a.account_balance
           FROM customers c JOIN accounts a ON c.customer_id = a.customer_id
           WHERE c.join_date LIKE '2023%' AND a.account_balance > 100000;""",

    "Q5: Total transaction volume by type":
        """SELECT txn_type, SUM(amount) AS total_volume FROM transactions
           GROUP BY txn_type ORDER BY total_volume DESC;""",

    "Q6: Accounts with >3 failed txns in a month":
        """SELECT customer_id, strftime('%Y-%m', txn_time) AS month, COUNT(*) AS failed_count
           FROM transactions WHERE LOWER(status) = 'failed'
           GROUP BY customer_id, month HAVING COUNT(*) > 3;""",

    "Q7: Top 5 branches by txn volume (last 6 months)":
        """SELECT b.Branch_Name, SUM(t.amount) AS total_volume
           FROM transactions t JOIN customers c ON t.customer_id = c.customer_id
           JOIN branches b ON c.city = b.City
           WHERE DATE(t.txn_time) >= DATE('now','-6 months')
           GROUP BY b.Branch_Name ORDER BY total_volume DESC LIMIT 5;""",

    "Q8: Accounts with >=5 high-value txns (>200000)":
        """SELECT customer_id, COUNT(*) AS high_value_count FROM transactions
           WHERE amount > 200000 GROUP BY customer_id HAVING COUNT(*) >= 5;""",

    "Q9: Avg loan amount & interest by loan type":
        """SELECT Loan_Type, AVG(Loan_Amount) AS avg_amount, AVG(Interest_Rate) AS avg_rate
           FROM loans GROUP BY Loan_Type;""",

    "Q10: Customers holding >1 active/approved loan":
        """SELECT Customer_ID, COUNT(*) AS active_loans FROM loans
           WHERE Loan_Status IN ('Active','Approved')
           GROUP BY Customer_ID HAVING COUNT(*) > 1;""",

    "Q11: Top 5 customers with highest outstanding loan amount":
        """SELECT Customer_ID, SUM(Loan_Amount) AS total_outstanding FROM loans
           WHERE Loan_Status != 'Closed'
           GROUP BY Customer_ID ORDER BY total_outstanding DESC LIMIT 5;""",

    "Q12: Branch with highest total account balance":
        """SELECT b.Branch_Name, SUM(a.account_balance) AS total_balance
           FROM accounts a JOIN customers c ON a.customer_id = c.customer_id
           JOIN branches b ON c.city = b.City
           GROUP BY b.Branch_Name ORDER BY total_balance DESC LIMIT 1;""",

    "Q13: Branch performance summary":
        """SELECT b.Branch_Name,
                  COUNT(DISTINCT c.customer_id) AS total_customers,
                  COUNT(DISTINCT l.Loan_ID) AS total_loans,
                  COALESCE(SUM(t.amount),0) AS transaction_volume
           FROM branches b
           LEFT JOIN customers c ON c.city = b.City
           LEFT JOIN loans l ON l.Branch = b.Branch_Name OR l.Branch = b.City
           LEFT JOIN transactions t ON t.customer_id = c.customer_id
           GROUP BY b.Branch_Name;""",

    "Q14: Issue categories with longest avg resolution time":
        """SELECT Issue_Category,
                  AVG(julianday(Date_Closed) - julianday(Date_Opened)) AS avg_days
           FROM support_tickets WHERE Date_Closed IS NOT NULL
           GROUP BY Issue_Category ORDER BY avg_days DESC;""",

    "Q15: Support agents resolving most critical tickets (rating >=4)":
        """SELECT Support_Agent, COUNT(*) AS resolved_critical FROM support_tickets
           WHERE Priority = 'Critical' AND Customer_Rating >= 4
           GROUP BY Support_Agent ORDER BY resolved_critical DESC;"""
}

# ===========================
# Streamlit App Starts Here
# ===========================
st.set_page_config(page_title="BankSight", layout="wide")

# Auto-create DB if missing
if not DB_PATH.exists():
    with st.spinner("Creating database from data/ folder..."):
        created = create_database_from_data()
        if not created:
            st.warning("Database was not created. Check your data/ folder and refresh.")

# Sidebar Navigation
st.sidebar.markdown("## 🏦 BankSight Navigation")
st.sidebar.markdown("**Go to:**")
page = st.sidebar.radio("", [
    "🏠 Introduction",
    "📊 View Tables",
    "🔍 Filter Data",
    "✏️ CRUD Operations",
    "💰 Credit / Debit Simulation",
    "🧠 Analytical Insights",
    "👩‍💻 About Creator"
])

# ===========================
# Page: Introduction
# ===========================
if page == "🏠 Introduction":
    st.title("🏦 BankSight: Transaction Intelligence Dashboard")
    st.subheader("Project Overview")
    st.write("""
        **Purpose:**
        BankSight is a dedicated financial analytics and simulation system built using a lightweight and efficient technology stack:
        - **Python** for backend logic
        - **Streamlit** for rapid dashboard development and user interface
        - **SQLite3** for data persistence

        This project goes beyond basic viewing — it provides a complete platform for users (such as internal analysts or bank staff) to:
        - Explore core banking entities (Customers, Accounts, Transactions, Loans)
        - Perform essential **CRUD** (Create, Read, Update, Delete) operations
        - Simulate key financial actions (deposits & withdrawals)
        - Gain immediate **analytical insights** through SQL queries
    """)
    st.markdown("**Datasets included:** customers, accounts, transactions, branches, loans, credit_cards, support_tickets.")
    st.info("Use the left sidebar to navigate between pages.")

# ===========================
# Page: View Tables
# ===========================
elif page == "📊 View Tables":
    st.header("📊 View Tables")

    tables_available = get_tables()

    if not tables_available:
        st.error("No tables found in the database. Make sure your data/ folder has CSV/JSON files and restart.")
    else:
        selected = st.selectbox("Select table to view", options=tables_available)
        limit = st.number_input("Rows to load", min_value=50, max_value=200000, value=1000, step=50)
        df = read_table(selected, limit=int(limit))

        if df.empty:
            st.warning("No data found in table: " + selected)
        else:
            st.write(f"Showing **{len(df)}** rows from `{selected}` table")
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "⬇️ Download as CSV",
                df.to_csv(index=False).encode(),
                f"{selected}.csv",
                "text/csv"
            )

# ===========================
# Page: Filter Data
# ===========================
elif page == "🔍 Filter Data":
    st.header("🔍 Filter Data")

    tables_available = get_tables()

    if not tables_available:
        st.error("No tables found in the database.")
    else:
        selected_table = st.selectbox("Select Table to Filter", options=tables_available)
        df = read_table(selected_table, limit=50000)

        if df.empty:
            st.warning("No data found in table: " + selected_table)
        else:
            st.markdown("**Select columns and values to filter:**")
            filters = {}

            for col in df.columns:
                if df[col].dtype == object or df[col].nunique() <= 50:
                    unique_vals = sorted(df[col].dropna().astype(str).unique().tolist())
                    selected_val = st.selectbox(f"{col}:", options=["(All)"] + unique_vals, key=f"filter_{col}")
                    if selected_val != "(All)":
                        filters[col] = selected_val

                elif pd.api.types.is_numeric_dtype(df[col]):
                    mn = float(df[col].min(skipna=True))
                    mx = float(df[col].max(skipna=True))
                    if mn < mx:
                        rng = st.slider(f"{col} range:", mn, mx, (mn, mx), key=f"filter_{col}")
                        filters[col] = ("range", rng)

                elif "date" in col.lower() or "time" in col.lower():
                    try:
                        dmin = pd.to_datetime(df[col], errors='coerce').min().date()
                        dmax = pd.to_datetime(df[col], errors='coerce').max().date()
                        start = st.date_input(f"{col} from:", value=dmin, key=f"filter_{col}_start")
                        end   = st.date_input(f"{col} to:", value=dmax, key=f"filter_{col}_end")
                        filters[col] = ("date", start, end)
                    except Exception:
                        pass

            result = df.copy()
            for col, fval in filters.items():
                try:
                    if isinstance(fval, tuple):
                        if fval[0] == "range":
                            result = result[(result[col] >= fval[1][0]) & (result[col] <= fval[1][1])]
                        elif fval[0] == "date":
                            result = result[
                                (pd.to_datetime(result[col], errors='coerce').dt.date >= fval[1]) &
                                (pd.to_datetime(result[col], errors='coerce').dt.date <= fval[2])
                            ]
                    else:
                        result = result[result[col].astype(str) == fval]
                except Exception:
                    pass

            st.markdown("---")
            st.write(f"**Filtered rows: {len(result)}**")
            st.dataframe(result, use_container_width=True)

            if not result.empty:
                st.download_button(
                    "⬇️ Download Filtered Data as CSV",
                    result.to_csv(index=False).encode(),
                    f"{selected_table}_filtered.csv",
                    "text/csv"
                )

# ===========================
# Page: CRUD Operations
# ===========================
elif page == "✏️ CRUD Operations":
    st.header("✏️ CRUD Operations")

    tables_available = get_tables()
    if not tables_available:
        st.error("No tables found in the database.")
    else:
        table = st.selectbox("Choose table", options=tables_available)
        mode  = st.radio("Select Operation", ["Create", "Read", "Update", "Delete"], horizontal=True)

        schema_df = read_sql_query(f"PRAGMA table_info({table});")
        cols = [row['name'] for _, row in schema_df.iterrows()] if not schema_df.empty else []

        pk_col = None
        if not schema_df.empty:
            for _, row in schema_df.iterrows():
                if row.get('pk') == 1 or str(row.get('pk')) == '1' or 'id' in str(row['name']).lower():
                    pk_col = row['name']
                    break
        if not pk_col and cols:
            pk_col = cols[0]

        st.markdown("---")

        if mode == "Create":
            st.subheader("➕ Create New Record")
            new = {}
            for c in cols:
                new[c] = st.text_input(f"{c}", key=f"create_{c}")
            if st.button("Insert Record", type="primary"):
                payload = {k: v for k, v in new.items() if v != ""}
                try:
                    insert_record(table, payload)
                    st.success("Record inserted successfully!")
                except Exception as e:
                    st.error("Insert failed: " + str(e))

        elif mode == "Read":
            st.subheader("📖 Read / Browse Records")
            limit = st.number_input("Number of rows", 10, 10000, 500)
            df = read_table(table, limit=int(limit))
            if df.empty:
                st.warning("No data found.")
            else:
                st.dataframe(df, use_container_width=True)
                st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(), f"{table}.csv", "text/csv")

        elif mode == "Update":
            st.subheader("✏️ Update Record")
            st.info(f"Primary key column: **{pk_col}**")
            pk_val = st.text_input("Enter primary key value to update")
            updates = {}
            for c in cols:
                if c == pk_col:
                    continue
                updates[c] = st.text_input(f"New value for `{c}` (leave blank to skip)", key=f"upd_{c}")
            if st.button("Execute Update", type="primary"):
                upd_payload = {k: v for k, v in updates.items() if v != ""}
                if not upd_payload:
                    st.warning("Please enter at least one value to update.")
                else:
                    try:
                        update_record(table, pk_col, pk_val, upd_payload)
                        st.success("Record updated successfully!")
                    except Exception as e:
                        st.error("Update failed: " + str(e))

        elif mode == "Delete":
            st.subheader("🗑️ Delete Record")
            st.info(f"Primary key column: **{pk_col}**")
            pk_val = st.text_input("Enter primary key value to delete")
            if st.button("Delete Record", type="primary"):
                try:
                    delete_record(table, pk_col, pk_val)
                    st.success("Record deleted successfully!")
                except Exception as e:
                    st.error("Delete failed: " + str(e))

# ===========================
# Page: Credit / Debit Simulation
# ===========================
elif page == "💰 Credit / Debit Simulation":
    st.header("💰 Credit / Debit Simulation")
    st.markdown("Enter a `customer_id` to load the account balance, then deposit or withdraw.")

    cid = st.text_input("Customer ID")

    if st.button("Load Balance"):
        df_acc = read_sql_query(f"SELECT * FROM accounts WHERE customer_id = '{cid}'")
        if df_acc.empty:
            st.error("Account not found for customer_id: " + str(cid))
        else:
            st.session_state["curr_balance"] = float(df_acc.iloc[0]["account_balance"])
            st.session_state["curr_cid"] = cid
            st.success(f"Balance loaded: ₹{st.session_state['curr_balance']:,.2f}")

    if "curr_balance" in st.session_state:
        st.metric("Current Balance", f"₹{st.session_state['curr_balance']:,.2f}")
        amt = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        op  = st.selectbox("Operation", ["Deposit", "Withdraw"])

        if st.button("Execute Transaction", type="primary"):
            cur    = st.session_state["curr_balance"]
            newbal = cur + amt if op == "Deposit" else cur - amt

            if op == "Withdraw" and newbal < 1000:
                st.error("Minimum balance ₹1,000 would be violated. Transaction aborted.")
            elif amt <= 0:
                st.warning("Please enter an amount greater than 0.")
            else:
                try:
                    engine = get_engine()
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE accounts SET account_balance = :bal, last_updated = :dt WHERE customer_id = :cid"),
                            {"bal": newbal, "dt": datetime.datetime.utcnow().isoformat(), "cid": st.session_state["curr_cid"]}
                        )
                    st.session_state["curr_balance"] = newbal
                    read_table.clear()
                    read_sql_query.clear()
                    st.success(f"Transaction successful! New balance: ₹{newbal:,.2f}")
                except Exception as e:
                    st.error("Transaction failed: " + str(e))

# ===========================
# Page: Analytical Insights
# ===========================
elif page == "🧠 Analytical Insights":
    st.header("🧠 Analytical Insights")
    st.markdown("Select a pre-built SQL query to explore banking insights.")

    selected = st.selectbox("Choose an insight", list(SQL_QUERIES.keys()))

    if selected:
        with st.expander("View SQL Query"):
            st.code(SQL_QUERIES[selected], language="sql")

        dfq = read_sql_query(SQL_QUERIES[selected])
        if dfq.empty:
            st.warning("Query returned no rows. The required tables may be missing.")
        else:
            st.dataframe(dfq, use_container_width=True)
            st.download_button(
                "⬇️ Download Result as CSV",
                dfq.to_csv(index=False).encode(),
                "insight.csv",
                "text/csv"
            )

# ===========================
# Page: About Creator
# ===========================
elif page == "👩‍💻 About Creator":
    st.header("👩‍💻 About the Creator")
    st.markdown("""
    **Name:** Rupali Rakh

    **Skills:** Python · SQL · Streamlit · Data Analysis · Banking Analytics

    **Project:** BankSight — Transaction Intelligence Dashboard

    **Contact:** rupalirakh@gmail.com
    """)
    st.info("This app is a demo project. Do not store production PII in a public repository.")
