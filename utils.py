import pandas as pd
import sqlite3
import requests
from dateutil.parser import parse
from datetime import datetime
import folium
from folium.plugins import MarkerCluster

# --- DATABASE FUNCTIONS ---

def create_connection():
    conn = sqlite3.connect('database.db')
    return conn

def get_sqlite_tables_with_counts():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Step 1: Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    # Step 2: For each table, get row count
    table_counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        table_counts[table] = count

    conn.close()
    return table_counts

def save_dataframe_to_sqlite(df, table_name):
    conn = create_connection()
    cursor = conn.cursor()

    # --- CHECK IF TABLE EXISTS ---
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    table_exists = cursor.fetchone() is not None

    if table_exists:
        # --- Get existing columns ---
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [row[1] for row in cursor.fetchall()]

        # --- Add missing columns dynamically ---
        for col in df.columns:
            if col not in existing_columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN [{col}] TEXT")

        conn.commit()
        # --- Append data ---
        df.to_sql(table_name, conn, if_exists='append', index=False)
    else:
        # --- First time: create table ---
        df.to_sql(table_name, conn, if_exists='replace', index=False)

    conn.close()

def load_dataframe_from_sqlite(table_name, selected_column, start_date, end_date):
    conn = create_connection()
    datetime_headers = []
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    for header in df.columns:
        print(header)
        if 'datetime' in header.lower():
            datetime_headers.append(header)
    query = f"""
    SELECT * FROM {table_name}
    WHERE DATE([{datetime_headers[selected_column]}]) BETWEEN ? AND ?
    """
    df = pd.read_sql_query(query, conn, params=[start_date, end_date])
    conn.close()

    #st.write(f"Records between {start_date} and {end_date}: {len(df)} rows")
    #selected_columns = st.sidebar.multiselect("Select Columns", options=df.columns.tolist(), default=df.columns.tolist())
    #st.dataframe(df[selected_columns])
    
    #conn.close()
    return df

# --- HEADER DETECTION FUNCTIONS ---

def is_potential_datetime(s):
    try:
        parse(s, fuzzy=False)
        return True
    except (ValueError, TypeError):
        return False

def detect_datetime_format(s):
    known_datetime_formats = [
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%Y.%m.%d",
        "%m.%d.%Y",
        "%d.%m.%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %I:%M %p",
        "%d-%m-%Y %H:%M",
        "%Y%m%d",
        "%d%m%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%a, %d %b %Y %H:%M:%S",
        "%A, %d %B %Y %H:%M:%S",
        "%Y-%j",
        "%H:%M:%S",
        "%I:%M:%S %p",
        "%H:%M",
        "%I:%M %p",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m-%d-%Y %H:%M:%S",
        "%b %d %H:%M:%S",
        "%Y-%m-%d %I:%M %p",
        "%A, %d-%b-%y %H:%M:%S %Z",
        "%m/%d/%y",
        "%d/%m/%y",
        "%Y/%m/%d %H:%M:%S",
        "%y-%m-%d",
        "%d-%b-%Y",
        "%d-%b-%Y %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M",
        "%d %B %Y, %H:%M",
        "%b %d %Y %H:%M:%S",
        "%A, %B %d, %Y",
        "%m/%d/%Y %H:%M:%S %p",
        "%d-%m-%y %I:%M %p",
        "%Y-%b-%d"
    ]
    for fmt in known_datetime_formats:
        try:
            datetime.strptime(s, fmt)
            return fmt
        except ValueError:
            continue
    return None

def find_header(dframe):
    header_dict={'Latitude':['lat',False],'Longitude':['lon',False],'Accuracy (m)':['accuracy',False]}
    for header in dframe.keys():
        key_found=False
        for dkey in header_dict.keys():
            if header_dict[dkey][1]: continue
            if any(header_dict[dkey][0].lower() in word.lower() for word in header.split()):
                header_dict[dkey] = [header,True]
                key_found=True
        sample = str(dframe[header][0]).split(":")
        if key_found: continue
        if len(sample) == 6 and len(sample[3]) == 2:
            header_dict["MAC Address"] = [header,True]
            continue
        if is_potential_datetime(dframe[header][0]):
            dt_fmt = detect_datetime_format(dframe[header][0])
            if dt_fmt:
                header_dict[header+"~DateTime~"+dt_fmt] = [header,True]
    return header_dict

# --- OTHER FUNCTIONS ---

def load_files(files):
    dataframes = []
    for file in files:
        df = pd.read_csv(file)
        df['Source Filename'] = file.name
        dataframes.append(df)
    return pd.concat(dataframes, ignore_index=True)

def find_same_devices(df):
    mac_counts = df['MAC Address'].value_counts()
    return df[df['MAC Address'].isin(mac_counts[mac_counts > 1].index)]

def find_different_devices(df):
    unique_macs = df['MAC Address'].drop_duplicates()
    return pd.concat([df[df['MAC Address'] == mac] for mac in unique_macs if len(df[df['MAC Address'] == mac]) == 1], ignore_index=True)

def find_new_devices(df):
    mac_counts = df['MAC Address'].value_counts()
    return df[df['MAC Address'].isin(mac_counts[mac_counts == 1].index)]

def get_mac_manufacturer(mac):
    try:
        response = requests.get(f"https://api.macvendors.com/{mac}")
        return response.text if response.status_code == 200 else "Unknown"
    except requests.exceptions.RequestException:
        return "Unknown"

def enrich_with_manufacturer(df):
    df['Manufacturer'] = df['MAC Address'].apply(lambda x: get_mac_manufacturer(str(x)[:8]))
    return df

def plot_devices_on_map(df):
    m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=(row['Latitude'], row['Longitude']),
            radius=5,
            color='blue',
            fill=True,
            fill_opacity=0.6,
            popup=f"MAC: {row['MAC Address']}\nAccuracy: {row.get('Accuracy (m)', '75m')}"
        ).add_to(marker_cluster)
    return m

def export_to_html(df, filename="exported_page.html"):
    html_content = """<html><head><title>Export</title></head><body><h1>Data Export</h1><table border='1'>"""
    html_content += "<tr><th>MAC Address</th><th>Latitude</th><th>Longitude</th><th>Manufacturer</th></tr>"
    for _, row in df.iterrows():
        html_content += f"<tr><td>{row['MAC Address']}</td><td>{row['Latitude']}</td><td>{row['Longitude']}</td><td>{row['Manufacturer']}</td></tr>"
    html_content += "</table><iframe src='map.html' width='100%' height='500px'></iframe></body></html>"
    with open(filename, "w") as f:
        f.write(html_content)
