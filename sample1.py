# app.py
"""
BankSight — Full Streamlit dashboard (single-file, multipage)
Features:
 - Auto-create SQLite DB on first run from data/ CSVs & JSONs
 - View Tables (all datasets)
 - Filter Data (multi-column filters)
 - CRUD operations (create/read/update/delete)
 - Credit/Debit simulation (with min balance enforcement)
 - Analytical Insights (15 SQL queries)
 - Intro & About pages

Place your source files in ./data:
 - customers.csv
 - accounts.csv
 - transactions.csv
 - branches.json
 - loans.json
 - credit_cards.json
 - support_tickets.json

Run:
    streamlit run app.py
"""

import datetime
from pathlib import Path
from winreg import QueryValue
from sqlalchemy import Engine, create_engine
import streamlit as st
import sqlite3 
import pandas as pd
from scripts.app import SQL_QUERIES, create_database_from_data, get_engine


conn =sqlite3.connect("bankdata1.db")
cursor = conn.cursor


# Sidebar navigation (multipage)
nav_page = st.sidebar.radio("Navigation", [
    "🏠 Introduction",
    "📊 View Tables", 
    "🔍 Filter Data",
    "✏️ CRUD Operations",
    "💰 Credit / Debit Simulation",
    "🧠 Analytical Insights",
    "👩‍💻 About Creator"
],key="nav_page")



# ----------------------------------------------------------------------------------------
# Page: Introduction
# --------------------------------------------------------------------------------------
if nav_page == "🏠 Introduction":
    st.title("🏦 BankSight: Transaction Intelligence Dashboard")
    #st.header("BankSight — Transaction Intelligence Dashboard")
st.header("Project overview")
st.write("""
            **Purpose:**
            BankSight is a dedicated financial analytics and simulation system built using a lightweight and efficient technology stack:
            - Python for backend logic
            - Streamlit for rapid dashboard development and user interface
            - SQLite3 for data persistence

            This project goes beyond basic viewing, providing a complete platform for users (such as internal analysts or bank staff) to explore core banking entities (Customers, Accounts, Transactions, Loans), perform essential CRUD (Create, Read, Update, Delete) operations, simulate key financial actions, and gain immediate analytical insights.
        """)
st.markdown("**Datasets included:** customers, accounts, transactions, branches, loans, credit_cards, support_tickets.")
st.markdown("Use the left sidebar to navigate between pages.")






# --------------------------------------------------------------------------------------------
# Page: View Tables
# ------------------------------------------------------------------------------------------
if nav_page == "📊 View Tables":
    st.header("📊 View Tables")
AVAILABLE_TABLES = ["Customers", "Accounts", "Branches", "Transactions", "Loans", "Credit_Cards", "Support_Tickets"]
#st.markdown("View a Tables:")

# First, fetch available tables from your database
def get_available_tables(conn):
    # For SQLite
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)['name'].tolist()
 
    return tables

AVAILABLE_TABLES = get_available_tables(conn)

# 1. Create the Selection Box
selected_table = st.selectbox(
    "Choose a Database Table:",
    options=AVAILABLE_TABLES,
    index=0  # Default to the first table in the list
)

# 2. Display button and selected table data
if selected_table:
        df = pd.read_sql(f"SELECT * FROM {selected_table};", conn)
        st.dataframe(df, use_container_width=True)
else:
        st.warning("Please select a table first.")







# --------------------------------------------------------------------------------------
# Page: Filter Data
# --------------------------------------------------------------------------------------

if nav_page== "🔍 Filter Data":
    st.header("🔍 Filter Data")
    
if selected_table:
    # Get columns for filter dropdown
    df_sample = pd.read_sql(f"SELECT * FROM \"{selected_table}\" LIMIT 1;", conn)
    columns = df_sample.columns.tolist()
    
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        filter_col = st.selectbox("Filter Column:", columns)
    with col2:
        filter_value = st.text_input("Filter Value:")
    
    # Build dynamic filter query
    if filter_value:
        query = f"""
        SELECT * FROM "{selected_table}" 
        WHERE {filter_col} LIKE '%{filter_value}%' 
        LIMIT 1000;
        """
    else:
        query = f'SELECT * FROM "{selected_table}" LIMIT 1000;'
    
    # Display filtered results
    df = pd.read_sql(query, conn)
    st.dataframe(df, use_container_width=True)
    #st.caption(f"📊 **{len(df)} rows** filtered from **{selected_table}**")









# --------------------------------------------------------------------------------------
# Page: CRUD Operation
# --------------------------------------------------------------------------------------

if nav_page == "✏️ CRUD Operations":
    st.header("✏️ CRUD Operations")

another_radio = st.radio(
    "Choose Operation:",
    ["📊 View", "➕ Create", "✏️ Update", "🗑️ Delete"],
    index=0,
    horizontal=True,
      key="radio_2")

cursor = conn.cursor()

# 📊 VIEW: Show all tables selector
if another_radio == "📊 View":
    st.subheader("View Data")
    
    # Get all tables from database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    if not tables:
        st.warning("⚠️ No tables found in database")
    else:
        # Let user select table to view
        selected_table = st.selectbox("Select Table:", tables)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            ""
            #if st.button("🔄 Refresh", use_container_width=True):
               # st.rerun()
        
        try:
            # Fixed: Use cursor instead of conn.query()
            cursor.execute(f'SELECT * FROM "{selected_table}"')
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f'PRAGMA table_info("{selected_table}")')
            columns = [col[1] for col in cursor.fetchall()]
            
            import pandas as pd
            df = pd.DataFrame(rows, columns=columns)
            st.dataframe(df, use_container_width=True)
            st.info(f"Showing {len(df)} records from '{selected_table}'")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")



if another_radio == "➕ Create":
    st.subheader("➕ Create New Record")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    if not tables:
        st.warning("⚠️ No tables found.")
    else:
        selected_table = st.selectbox("Select Table:", tables)
        
        # ✅ Get ALL table info including primary key column name
        cursor.execute(f'PRAGMA table_info("{selected_table}")')
        columns_info = cursor.fetchall()
        
        # ✅ Show primary key info but DON'T include in form inputs
        pk_column = None
        input_columns = []
        for col in columns_info:
            if col[5] == 1:  # col[5] = pk (1=True)
                pk_column = col[1]  # Store PK column name (customer_id)
                st.info(f"🔑 **Primary Key**: `{pk_column}` (Auto-generated)")
            else:
                input_columns.append((col[1], col[2]))  # Add non-PK columns
        
        with st.form("create_form", clear_on_submit=True):
            form_data = {}
            
            for col_name, col_type in input_columns:
                col_type_str = str(col_type).upper()
                if "TEXT" in col_type_str:
                    form_data[col_name] = st.text_input(col_name, placeholder=f"Enter {col_name}")
                elif "INTEGER" in col_type_str:
                    form_data[col_name] = st.number_input(col_name, min_value=0, step=1, format="%d")
                elif "REAL" in col_type_str:
                    form_data[col_name] = st.number_input(col_name, min_value=0.0, step=0.01, format="%.2f")
                else:
                    form_data[col_name] = st.text_input(col_name, placeholder=f"Enter {col_name}")
            
            submitted = st.form_submit_button("➕ Add Record", use_container_width=True, type="primary")
            
            if submitted:
                values = [form_data[col] for col in form_data.keys()]
                if all(val for val in values):
                    columns_list = list(form_data.keys())
                    placeholders = ','.join(['?' for _ in columns_list])
                    query = f'INSERT INTO "{selected_table}" ({",".join(columns_list)}) VALUES ({placeholders})'
                    
                    try:
                        new_cursor = conn.cursor()
                        new_cursor.execute(query, values)
                        new_id = new_cursor.lastrowid
                        conn.commit()
                        new_cursor.close()
                        
                        # ✅ Show EXACT primary key name from table
                        st.success(f"✅ Record added to '{selected_table}'! **{pk_column}: {new_id}**")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Insert failed: {str(e)}")
                        conn.rollback()
                else:
                    st.error("❌ Please fill **ALL fields** before submitting!")

# ✏️ UPDATE: Works with tables WITHOUT primary key
if another_radio == "✏️ Update":
    st.subheader("✏️ Update Record")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    if not tables:
        st.warning("⚠️ No tables found.")
    else:
        selected_table = st.selectbox("Select Table:", tables)
        
        # Get first column as identifier (works for any table)
        cursor.execute(f'PRAGMA table_info("{selected_table}")')
        columns_info = cursor.fetchall()
        id_column = columns_info[0][1]  # Use FIRST column as identifier
        
        st.info(f"🔑 **Identifier**: `{id_column}` (First column)")
        
        # Show current records
        cursor.execute(f'SELECT * FROM "{selected_table}" ORDER BY "{id_column}" ASC')
        rows = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        
        import pandas as pd
        df = pd.DataFrame(rows, columns=columns)
        st.dataframe(df, use_container_width=True)
        
        # Record selector using first column values
        first_col_values = [row[0] for row in rows]
        selected_id = st.selectbox("Select Record ID to Update:", first_col_values)
        
        if selected_id is not None:
            # Load current record
            cursor.execute(f'SELECT * FROM "{selected_table}" WHERE "{id_column}"=?', (selected_id,))
            current_record = cursor.fetchone()
            
            with st.form("update_form", clear_on_submit=True):
                form_data = {}
                update_columns = columns  # Update ALL columns
                
                for i, col_name in enumerate(update_columns):
                    current_val = current_record[i] if current_record else ""
                    col_info = next(col for col in columns_info if col[1] == col_name)
                    col_type = col_info[2]
                    col_type_str = str(col_type).upper()
                    
                    if "TEXT" in col_type_str:
                        form_data[col_name] = st.text_input(col_name, value=str(current_val))
                    elif "INTEGER" in col_type_str:
                        form_data[col_name] = st.number_input(col_name, value=int(current_val) if current_val else 0, step=1)
                    elif "REAL" in col_type_str:
                        form_data[col_name] = st.number_input(col_name, value=float(current_val) if current_val else 0.0, step=0.01)
                    else:
                        form_data[col_name] = st.text_input(col_name, value=str(current_val))
                
                submitted = st.form_submit_button("✏️ Update Record", use_container_width=True, type="primary")
                
                if submitted:
                    # Build UPDATE using first column as WHERE
                    set_clause = ",".join([f'"{col}"=?' for col in update_columns])
                    query = f'UPDATE "{selected_table}" SET {set_clause} WHERE "{id_column}"=?'
                    values = [form_data[col] for col in update_columns] + [selected_id]
                    
                    try:
                        new_cursor = conn.cursor()
                        new_cursor.execute(query, values)
                        conn.commit()
                        new_cursor.close()
                        
                        st.success(f"✅ Record **{id_column}: {selected_id}** updated!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Update failed: {str(e)}")
                        conn.rollback()

# 🗑️ DELETE: Fixed Cancel button
if another_radio == "🗑️ Delete":
    st.subheader("🗑️ Delete Record")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    if not tables:
        st.warning("⚠️ No tables found.")
    else:
        selected_table = st.selectbox("Select Table:", tables)
        
        cursor.execute(f'PRAGMA table_info("{selected_table}")')
        columns_info = cursor.fetchall()
        id_column = columns_info[0][1]
        
        st.info(f"🔑 **Identifier**: `{id_column}`")
        
        # Show records preview
        cursor.execute(f'SELECT * FROM "{selected_table}" ORDER BY "{id_column}" ASC')
        rows = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        
        import pandas as pd
        df = pd.DataFrame(rows, columns=columns)
        st.dataframe(df, use_container_width=True)
        
        # Record selector
        first_col_values = [row[0] for row in rows]
        selected_id = st.selectbox("⚠️ Select Record to DELETE:", [""] + first_col_values)
        
        # ✅ FIXED: Use session_state to track delete state
        if 'show_delete_confirm' not in st.session_state:
            st.session_state.show_delete_confirm = False
        
        if selected_id and not st.session_state.show_delete_confirm:
            if st.button("⚠️ Show Delete Confirmation", use_container_width=True):
                st.session_state.show_delete_confirm = True
                st.rerun()
        
        # Confirmation section
        if st.session_state.show_delete_confirm and selected_id:
            st.warning(f"**⚠️ Confirm delete record {id_column}: {selected_id}?**")
            
            # Show record details
            cursor.execute(f'SELECT * FROM "{selected_table}" WHERE "{id_column}"=?', (selected_id,))
            record_to_delete = cursor.fetchone()
            st.json(dict(zip(columns, record_to_delete)))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ CONFIRM DELETE", type="primary", use_container_width=True):
                    try:
                        new_cursor = conn.cursor()
                        new_cursor.execute(f'DELETE FROM "{selected_table}" WHERE "{id_column}"=?', (selected_id,))
                        deleted_count = new_cursor.rowcount
                        conn.commit()
                        new_cursor.close()
                        
                        st.session_state.show_delete_confirm = False  # Reset state
                        st.success(f"✅ **{deleted_count} record** deleted!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Delete failed: {str(e)}")
                        conn.rollback()
            
            with col2:
                if st.button("❌ CANCEL", use_container_width=True):
                    st.session_state.show_delete_confirm = False  # ✅ Reset state
                    st.success("❌ Delete cancelled!")
                    st.rerun()
        elif st.session_state.show_delete_confirm and not selected_id:
            st.session_state.show_delete_confirm = False
            st.rerun()


# ----------------------------------------------------------------------------------------
# Page: Credit / Debit Simulation
# ----------------------------------------------------------------------------------------
import pandas as pd
from sqlalchemy import text
import datetime

if nav_page == "💰 Credit / Debit Simulation":
    st.header("💰 Credit / Debit Simulation")
    
    cid = st.text_input("Customer ID", key="cid_sim")
    
    if st.button("Load balance", key="load_sim"):
        try:
            # ✅ FIXED: Use plain string for pd.read_sql_query
            df_acc = pd.read_sql_query(
                f"SELECT * FROM accounts WHERE customer_id = '{cid}'",  # Plain SQL string
                con=get_engine()
            )
            if df_acc.empty:
                st.error(f"❌ Account not found: {cid}")
            else:
                st.session_state["curr_balance"] = float(df_acc.iloc[0]["account_balance"])
                st.session_state["loaded_cid"] = cid
                st.success(f"✅ Loaded: ₹{st.session_state['curr_balance']:.2f}")
        except Exception as e:
            st.error(f"❌ Load failed: {str(e)}")
    
    # Show current balance
    if "curr_balance" in st.session_state:
        st.info(f"💰 Current: ₹{st.session_state['curr_balance']:.2f}")
    
    col1, col2 = st.columns(2)
    with col1:
        amt = st.number_input("Amount", min_value=0.01, format="%.2f", key="amt_sim")
    with col2:
        op = st.selectbox("Operation", ["Deposit 💳", "Withdraw 🪙"], key="op_sim")
    
    if st.button("Execute transaction", key="exec_sim"):
        if "curr_balance" not in st.session_state:
            st.error("⚠️ Load balance first!")
        elif st.session_state.get("loaded_cid") != cid:
            st.error("⚠️ Wrong customer ID!")
        else:
            cur = st.session_state["curr_balance"]
            if "Deposit" in op:
                newbal = cur + amt
            else:
                newbal = cur - amt
                if newbal < 1000:
                    st.error("❌ Min balance ₹1000 required!")
                else:
                    # ✅ UPDATE uses text() correctly (direct conn.execute)
                    try:
                        engine = get_engine()
                        with engine.begin() as conn:
                            conn.execute(
                                text("UPDATE accounts SET account_balance = :bal, last_updated = :dt WHERE customer_id = :cid"),
                                {"bal": newbal, "dt": datetime.datetime.utcnow().isoformat(), "cid": cid}
                            )
                        st.session_state["curr_balance"] = newbal
                        st.success(f"✅ New balance: ₹{newbal:.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Update failed: {str(e)}")



# ------------------------------------------------------------------------------
# Page: Analytical Insights
# -----------------------------------------------------------------------------------------
if nav_page == "🧠 Analytical Insights":
    st.header("🧠 Analytical Insights")
  
DATABASE_URL = "sqlite:///bankdata1.db"  # Example for SQLite, replace as needed

# Engine setup
engine = create_engine(DATABASE_URL)

SQL_QUERIES = {
    "Q1: Customers per city & avg balance":
        """
        SELECT c.city,
        COUNT(*) AS total_customers,
        ROUND(AVG(a.account_balance),2) AS avg_balance
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        GROUP BY c.city
        ORDER BY avg_balance DESC;
        """,

    "Q2: Account type holding highest total balance":
        """
        SELECT c.account_type,
        SUM(a.account_balance) AS total_balance
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        GROUP BY c.account_type
        ORDER BY total_balance DESC;
        """,

    "Q3: Top 10 customers by total balance":
        """
        SELECT c.customer_id, c.name, c.city, a.account_balance
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        ORDER BY a.account_balance DESC
        LIMIT 10;
        """,

    "Q4: Customers in 2023 with balance > 100000":
        """
        SELECT c.customer_id, c.name, c.city, c.join_date, a.account_balance
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        WHERE c.join_date LIKE '2023%' AND a.account_balance > 100000;
        """,

    "Q5: Total transaction volume by type":
        """
        SELECT txn_type, SUM(amount) AS total_volume
        FROM transactions
        GROUP BY txn_type
        ORDER BY total_volume DESC;
        """,

    "Q6: Accounts with >3 failed txns in a month":
        """
        SELECT customer_id, strftime('%Y-%m', txn_time) AS month, COUNT(*) AS failed_count
        FROM transactions
        WHERE LOWER(status) = 'failed'
        GROUP BY customer_id, month
        HAVING COUNT(*) > 3;
        """,

    "Q7: Top 5 branches by txn volume (last 6 months)":
        """
        SELECT b.Branch_Name, SUM(t.amount) AS total_volume
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        JOIN branches b ON c.city = b.City
        WHERE DATE(t.txn_time) >= DATE('now','-6 months')
        GROUP BY b.Branch_Name
        ORDER BY total_volume DESC
        LIMIT 5;
        """,

    "Q8: Accounts with >=5 high-value txns (>200000)":
        """
        SELECT customer_id, COUNT(*) AS high_value_count
        FROM transactions
        WHERE amount > 200000
        GROUP BY customer_id
        HAVING COUNT(*) >= 5;
        """,

    "Q9: Avg loan amount & interest by loan type":
        """
        SELECT Loan_Type, AVG(Loan_Amount) AS avg_amount, AVG(Interest_Rate) AS avg_rate
        FROM loans
        GROUP BY Loan_Type;
        """,

    "Q10: Customers holding >1 active/approved loan":
        """
        SELECT Customer_ID, COUNT(*) AS active_loans
        FROM loans
        WHERE Loan_Status IN ('Active', 'Approved')
        GROUP BY Customer_ID
        HAVING COUNT(*) > 1;
        """,

    "Q11: Top 5 customers with highest outstanding loan amount":
        """
        SELECT Customer_ID, SUM(Loan_Amount) AS total_outstanding
        FROM loans
        WHERE Loan_Status != 'Closed'
        GROUP BY Customer_ID
        ORDER BY total_outstanding DESC
        LIMIT 5;
        """,

    "Q12: Branch with highest total account balance":
        """
        SELECT b.Branch_Name, SUM(a.account_balance) AS total_balance
        FROM accounts a
        JOIN customers c ON a.customer_id = c.customer_id
        JOIN branches b ON c.city = b.City
        GROUP BY b.Branch_Name
        ORDER BY total_balance DESC
        LIMIT 1;
        """,

    "Q13: Branch performance summary":
        """
        SELECT b.Branch_Name,
            COUNT(DISTINCT c.customer_id) AS total_customers,
            COUNT(DISTINCT l.Loan_ID) AS total_loans,
            COALESCE(SUM(t.amount),0) AS transaction_volume
        FROM branches b
        LEFT JOIN customers c ON c.city = b.City
        LEFT JOIN loans l ON l.Branch = b.Branch_Name OR l.Branch = b.City
        LEFT JOIN transactions t ON t.customer_id = c.customer_id
        GROUP BY b.Branch_Name;
        """,

    "Q14: Issue categories with longest avg resolution time":
        """
        SELECT Issue_Category,
               AVG(julianday(Date_Closed) - julianday(Date_Opened)) AS avg_days
        FROM support_tickets
        WHERE Date_Closed IS NOT NULL
        GROUP BY Issue_Category
        ORDER BY avg_days DESC;
        """,

    "Q15: Support agents resolving most critical tickets (rating >=4)":
        """
        SELECT Support_Agent, COUNT(*) AS resolved_critical
        FROM support_tickets
        WHERE Priority = 'Critical' AND Customer_Rating >= 4
        GROUP BY Support_Agent
        ORDER BY resolved_critical DESC;
        """
}
def run_query(query):
    with engine.connect() as conn:
        result = conn.execute(st.text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df

#st.title("Banking Analytics Dashboard")

# Select query to run
selected_query = st.selectbox("Choose a query to view", list(SQL_QUERIES.keys()))

if st.button("Run Query"):
    query = SQL_QUERIES[selected_query]
    try:
        df = run_query(query)
        st.subheader(f"Results for: {selected_query}")
        st.dataframe(df)
    except Exception as e:
        #st.error(f"Database query failed: {e}")






# ---------------------------
# Page: About Creator
# ---------------------------
if nav_page == "👩‍💻 About Creator":
    st.header("About / Contact")
        st.markdown("""
                **Creator:** Rupali Rakh
    
                **Skills:** Python, SQL, Streamlit, Data Analysis, Banking Analytics
    
                **Contact:** rupalirakh@gmail.com
        """)
        st.info("This app is a demo.")

# ---------------------------
# End of app
# ---------------------------