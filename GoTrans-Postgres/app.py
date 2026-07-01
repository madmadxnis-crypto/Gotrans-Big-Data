import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Mengambil URL dari GitHub Secrets (nanti di-cloud)
# Kalau lokal, lu bisa ganti sementara ke URL Supabase lu
DATABASE_URL = st.secrets["SUPABASE_URL"]
engine = create_engine(DATABASE_URL)

st.title("Gotrans Operational Dashboard")

# Pilih tabel (bulan)
table_name = st.selectbox("Pilih Bulan Laporan:", ["2025_04", "2025_05", "2025_06"])

# Ambil data dari Supabase
if st.button("Tampilkan Data"):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, engine)
    st.write(f"Menampilkan data {table_name}")
    st.dataframe(df)