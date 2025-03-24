import streamlit as st
from utils import load_files, find_header, save_dataframe_to_sqlite, pd

st.title("📤 Data Upload & Store")

uploaded_files = st.file_uploader("Upload WiGLE CSV Files", accept_multiple_files=True, type=["csv"])

if uploaded_files:
    df = load_files(uploaded_files)
    st.write(f"Loaded {len(df)} records.")

    header_vars = find_header(df)
    inverted_headers = {v[0]: k for k, v in header_vars.items() if v[1]}
    st.write(inverted_headers)
    df = df.rename(columns=inverted_headers)
    for header in df.columns:
        if "~" in header:
            splitlist = header.split("~")
            dtstr = splitlist[2]
            df[header] = pd.to_datetime(df[header], format=dtstr, errors='coerce')
    df = df.dropna(subset=['MAC Address'])

    st.write("Cleaned Data:")
    st.dataframe(df)

    table_name = st.text_input("SQLite Table Name", value="wigle_data")
    if st.button("Store Data"):
        save_dataframe_to_sqlite(df, table_name)
        st.success(f"Data stored under table: `{table_name}`")
