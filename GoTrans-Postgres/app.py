import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = st.secrets["SUPABASE_URL"]
engine = create_engine(DATABASE_URL)

st.title("Gotrans Operational Dashboard")

# Pakai tanda strip (-) biar sama persis kayak nama file Excel lu
table_name = st.selectbox("Pilih Bulan Laporan:", ["2025-04", "2025-05", "2025-06", "2025-07"])

if st.button("Tampilkan Data"):
    # Tabel yang diawali angka di PostgreSQL wajib pakai kutip ganda ("")
    query = f'SELECT * FROM "{table_name}"'
    
    try:
        df = pd.read_sql(query, engine)
        st.write(f"Menampilkan data {table_name}")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Gagal menarik data: {e}")