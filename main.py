import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import streamlit as st

st.set_page_config(page_title="Simple Finance Application", page_icon=":money_with_wings:", layout="wide")

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }

if os.path.exists("categories.json"):
    with open("categories.json", "r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open("categories.json", "w") as f:
        json.dump(st.session_state.categories, f)

def categorize_transactions(df):
    df['Category'] = 'Uncategorized'
    for category, transactions in st.session_state.categories.items():
        if category == "Uncategorized" or not transactions:
            continue
        lower_transactions = [t.lower().strip() for t in transactions]
        for idx, row in df.iterrows():
            details = row['Details'].lower().strip()
            if any(t in details for t in lower_transactions):
                df.at[idx, 'Category'] = category
                break

    return df
        
def add_transaction_to_category(category, transaction):
    transaction = transaction.strip()
    if transaction and transaction not in st.session_state.categories[category]:
        st.session_state.categories[category].append(transaction)
        save_categories()
        return True
    return False


# st.title("Simple Finance Application")

def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        df['Amount'] = df['Amount'].str.replace(',', '').astype(float)
        df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')
        # st.write(df)
        # return df
        return categorize_transactions(df)
    except Exception as e:
        st.error(f"Error loading transactions: {e}")
        return None

def main():
    st.title("Simple Finance Application")

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            debits_df = df[df['Debit/Credit'] == 'Debit'].copy()
            credits_df = df[df['Debit/Credit'] == 'Credit'].copy()

            st.session_state.debits_df = debits_df.copy()

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Income (Credits)"])
            with tab1:
                new_category = st.text_input("Enter a new category")
                add_button = st.button("Add Category")
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                # st.write(debits_df)
                st.subheader("Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[["Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f Rupees", min_value=0),
                        "Category": st.column_config.SelectboxColumn("Category", options=list(st.session_state.categories.keys()))
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="debits_editor"
                )

                save_button = st.button("Save Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row['Category']
                        if new_category == st.session_state.debits_df.at[idx, 'Category']:
                            continue
                        
                        details = row['Details']
                        st.session_state.debits_df.at[idx, 'Category'] = new_category
                        add_transaction_to_category(new_category, details)
                
                st.subheader("Expense Summary")
                category_totals = st.session_state.debits_df.groupby('Category')['Amount'].sum().reset_index()
                category_totals = category_totals.sort_values(by='Amount', ascending=False)

                st.dataframe(category_totals, column_config={
                    "Amount": st.column_config.NumberColumn("Amount", format="%.2f Rupees", min_value=0)
                }, use_container_width=True, hide_index=True)

                st.subheader("Expense Trends")
                fig = px.pie(
                    category_totals,
                    values='Amount',
                    names='Category',
                    title='Expense Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Total Expenses")
                st.metric("Total Expenses", f"₹{category_totals['Amount'].sum():.2f}")
                    

            with tab2:
                st.subheader("Income")
                st.metric("Total Income", f"₹{credits_df['Amount'].sum():.2f}")
                st.write(credits_df)
    
    

if __name__ == "__main__":
    main()
