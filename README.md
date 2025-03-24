# 📡 WiGLE Data Analysis Streamlit App

A multi-page Streamlit application for uploading, storing, viewing, analyzing, and exporting WiGLE CSV data. The app supports SQLite database storage, MAC address analysis, datetime detection, device comparison, and map visualization.

---

## 🚀 Features

- **Upload & Store WiGLE CSV Files**
- **View & Analyze Stored Data**
- **Export Options**
- **MAC Address Manufacturer Lookup**
- **Map Visualization**

---

## 🗂️ Project Structure

```
wigle_streamlit_app/
├── streamlit_app.py
├── utils.py
├── database.db
├── pages/
│   ├── 1_Data_Upload_and_Store.py
│   └── 2_Data_View_and_Export.py
├── map.html
├── README.md
└── requirements.txt
```

---

## 💾 Installation & Setup

1. **Clone the repository:**

```bash
git clone <your-repo-url>
cd wigle_streamlit_app
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run the Streamlit app:**

```bash
streamlit run streamlit_app.py
```

---

## 📦 Dependencies

See `requirements.txt` for details.

---

## 📃 License

MIT License.
