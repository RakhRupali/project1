# project1
# 🏦 BankSight: Transaction Intelligence Dashboard

> A full-stack banking analytics application built with Python, SQL, and Streamlit — enabling real-time transaction insights, fraud detection, and interactive data management.

---

## 📌 Project Overview

Banks process millions of transactions daily. **BankSight** is a Banking Transaction Intelligence System that helps analysts and bank staff:

- Analyze customer demographics and transaction behavior
- Identify trends across account types, branches, and regions
- Detect anomalies and potentially fraudulent transactions
- Perform CRUD operations on accounts and transactions
- Simulate credit/debit operations with balance enforcement

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.x |
| Frontend | Streamlit |
| Database | SQLite3 |
| Data Processing | Pandas, SQLAlchemy |
| Version Control | Git & GitHub |

---

## 📁 Project Structure

```
project1/
│
├── sample1.py              # Main Streamlit app (all pages)
├── bankdata1.db            # SQLite database (auto-created on first run)
│
├── data/                   # Source datasets
│   ├── customers.csv
│   ├── accounts.csv
│   ├── transactions.csv
│   ├── loans.json
│   ├── credit_cards.json
│   ├── branches.json
│   └── support_tickets.json
│
└── README.md
```

---

## 📊 Datasets

| Dataset | Format | Description |
|---------|--------|-------------|
| `customers.csv` | CSV | Customer demographics — name, age, city, account type, join date |
| `accounts.csv` | CSV | Account balances and last updated timestamp |
| `transactions.csv` | CSV | Full transaction log — type, amount, status, timestamp |
| `loans.json` | JSON | Loan details — type, amount, interest rate, status |
| `credit_cards.json` | JSON | Card details — type, network, credit limit, balance |
| `branches.json` | JSON | Branch info — city, manager, employees, revenue, rating |
| `support_tickets.json` | JSON | Customer support records — issue, priority, resolution, rating |

---

## 🗄️ Database Schema (ER Overview)

```
customers ──────< accounts
    │
    └──────────< transactions
    │
    └──────────< loans
    │
    └──────────< credit_cards
    │
    └──────────< support_tickets

branches ──── linked via city/branch name
```

All tables are stored in `bankdata1.db` (SQLite) and auto-created on first run from the `data/` folder.

---

## 🚀 How to Run

### 1. Clone the repository
```bash
git clone https://github.com/RakhRupali/project1.git
cd project1
```

### 2. Install dependencies
```bash
pip install streamlit pandas sqlalchemy
```

### 3. Run the app
```bash
streamlit run sample1.py
```

The app will open at `http://localhost:8501` in your browser.

> **Note:** Make sure all dataset files are placed in a `data/` folder inside the project directory before running.

---

## 📱 App Pages

| Page | Description |
|------|-------------|
| 🏠 Introduction | Project overview, objectives, and datasets |
| 📊 View Tables | Browse all 6 datasets directly from the SQLite database |
| 🔍 Filter Data | Multi-column filtering on any table |
| ✏️ CRUD Operations | Create, Read, Update, Delete records from any table |
| 💰 Credit / Debit Simulation | Deposit or withdraw with minimum ₹1000 balance rule |
| 🧠 Analytical Insights | 15 live SQL queries across all banking domains |
| 👩‍💻 About Creator | Creator info and contact details |

---

## 🧠 Analytical Insights (15 SQL Queries)

### Customer & Account Analysis
- **Q1** — Customers per city and their average account balance
- **Q2** — Account type with the highest total balance
- **Q3** — Top 10 customers by total account balance
- **Q4** — Customers who joined in 2023 with balance above ₹1,00,000

### Transaction Behavior
- **Q5** — Total transaction volume by transaction type
- **Q6** — Accounts with more than 3 failed transactions in a month
- **Q7** — Top 5 branches by transaction volume (last 6 months)
- **Q8** — Accounts with 5 or more high-value transactions above ₹2,00,000

### Loan Insights
- **Q9** — Average loan amount and interest rate by loan type
- **Q10** — Customers holding more than one active or approved loan
- **Q11** — Top 5 customers with highest outstanding loan amounts

### Branch & Performance
- **Q12** — Branch with highest total account balance
- **Q13** — Branch performance summary (customers, loans, transaction volume)

### Support Tickets & Customer Experience
- **Q14** — Issue categories with the longest average resolution time
- **Q15** — Support agents who resolved the most critical tickets with high ratings (≥4)

---

## 🔍 Key Features

- **Live SQL execution** — every insight query runs directly against the SQLite database
- **Multi-level filtering** — filter any table by any column with instant results
- **Full CRUD support** — add, view, update, and delete records with validation
- **Credit/Debit simulation** — enforces ₹1,000 minimum balance rule on withdrawals
- **Fraud detection logic** — identifies accounts with repeated failed transactions

---

## 👩‍💻 About the Creator

**Rupali Rakh**  
Skills: Python, SQL, Streamlit, Data Analysis, Banking Analytics  
📧 rupalirakh@gmail.com  
🔗 [GitHub Profile](https://github.com/RakhRupali)

---

## 📄 License

This project is created for educational purposes as part of a data analytics training program.

