import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Gotrans Operational Dashboard")

# 1. Setup Koneksi ke Supabase
DATABASE_URL = st.secrets["SUPABASE_URL"]
engine = create_engine(DATABASE_URL)

# 2. Setup Sidebar
st.sidebar.header("Filter Laporan")
# Pastikan daftar bulan ini sesuai dengan nama tabel lu di Supabase
bulan = st.sidebar.selectbox("Pilih Bulan", ["2025-04", "2025-05", "2025-06", "2025-07"])

# 3. Tarik Data
if st.sidebar.button("Tampilkan Data"):
    query = f'SELECT * FROM "{bulan}"'
    
    try:
        df = pd.read_sql(query, engine)
        
        # 4. Tampilkan Metrik Utama
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Order / Resi", len(df))
        col2.metric("Status Data", "Berhasil Terhubung")
        col3.metric("Bulan Aktif", bulan)
        
        st.divider() # Garis pembatas biar rapi

        # 5. Tampilkan Tabel Mentah
        st.subheader("Data Raw Operasional")
        st.dataframe(df)
        
        st.info("💡 Next Step: Cek tabel di atas, lalu catat apa nama kolom untuk 'Tanggal Pengiriman' dan 'Tipe Armada' (biar kita bisa lanjut bikin grafik pie chart 20-foot/40-foot dan bar chart rute).")
        
    except Exception as e:
        st.error(f"Gagal menarik data: {e}")
