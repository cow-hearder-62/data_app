import streamlit as st
from utils import datetime, create_connection, get_sqlite_tables_with_counts, load_dataframe_from_sqlite, find_same_devices, find_different_devices, find_new_devices, plot_devices_on_map, enrich_with_manufacturer, export_to_html

st.title("📊 View & Export Data")



# if st.button("Query with Datetime Filter"):
#     conn = create_connection()
#     query = f"""
#     SELECT * FROM {table_name}
#     WHERE DATE([{selected_column}]) BETWEEN ? AND ?
#     """
#     df = pd.read_sql_query(query, conn, params=[start_date, end_date])
#     conn.close()

#     st.write(f"Records between {start_date} and {end_date}: {len(df)} rows")
#     selected_columns = st.sidebar.multiselect("Select Columns", options=df.columns.tolist(), default=df.columns.tolist())
#     st.dataframe(df[selected_columns])
first_container = st.container(height=250)
second_container = st.container(height=600)
# if 'second_container' not in st.session_state:
#     second_container = st.container(height=600)

# else: second_container = st.session_state['second_container']

with first_container:
    col0,col1,col2,col3,col4 = st.columns([0.5,0.5,1,1,1])
    with col0:
        buttonpress = st.button("Load Data", key="load_data")
    with col1:
        st.selectbox("DateTime Obj", options=[0,1], key="datetime_key", index=0)
    with col2:
        tables = get_sqlite_tables_with_counts()
        table_name = st.selectbox("SQLite Table", options=tables.items())
    with col3:
        sdate = st.date_input("Start Date", key="start_d")
        stime = st.time_input("Time", key='start_t')
        st.session_state["start_date"] = datetime.combine(sdate, stime)
        st.write(datetime.combine(sdate, stime))
    with col4:
        edate = st.date_input("End Date", key="end_d")
        etime = st.time_input("Time", key='end_t')
        st.session_state["end_date"] = datetime.combine(edate, etime)
        st.write(datetime.combine(edate, etime))
with second_container:
    start_date = st.session_state["start_date"]
    end_date = st.session_state["end_date"]
    if st.session_state["load_data"] == True:
        datetime_column = st.session_state['datetime_key']
        df = load_dataframe_from_sqlite(table_name[0], datetime_column, start_date, end_date)
        st.session_state['df'] = df
        st.write(f"Loaded {len(df)} records")
        selected_columns = st.multiselect("Select Columns", options=df.columns.tolist(), default=df.columns.tolist())
        st.dataframe(df[selected_columns])
        st.session_state['selected_columns'] = selected_columns

    capability = st.selectbox("Select Capability:", ["Find Same Devices", "Find Different Devices", "Find New Devices", "Plot Devices on Map"])
    if 'df' in st.session_state:
        selected_columns = st.session_state['selected_columns']
        df = st.session_state['df']
        if capability == "Find Same Devices":
            st.write(find_same_devices(df)[selected_columns])
        elif capability == "Find Different Devices":
            st.write(find_different_devices(df)[selected_columns])
        elif capability == "Find New Devices":
            st.write(find_new_devices(df)[selected_columns])
        elif capability == "Plot Devices on Map":
            enriched_df = enrich_with_manufacturer(df)
            map_obj = plot_devices_on_map(enriched_df)
            map_obj.save("map.html")
            st.success("Map saved as `map.html`")

        if st.button("Export to HTML"):
            export_to_html(df)
            st.success("HTML Export created")
