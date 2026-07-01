import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Konfigurasi Halaman (Wajib paling atas!)
st.set_page_config(page_title="Gotrans TMS Dashboard", page_icon="🚚", layout="wide")

# 2. HEADER: Logo dan Judul berdampingan
col_logo, col_judul = st.columns([1, 4]) # Rasio lebar kolom 1:4

with col_logo:
    # Menampilkan logo (pastikan nama file persis sama dengan yang di-upload)
    st.image("logo_gobel.jpg", use_container_width=True)

with col_judul:
    # Pakai HTML sedikit biar margin atasnya pas sama tinggi logo
    st.markdown("<h1 style='margin-top: -15px;'>Gotrans Operational Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("#### Logistik & Transport Management System (TMS)")

st.divider() # Garis pembatas

# 3. SETUP KONEKSI
DATABASE_URL = st.secrets["SUPABASE_URL"].strip()
engine = create_engine(DATABASE_URL)

# 4. SIDEBAR: Menu & Filter
st.sidebar.header("Navigasi")
# Ini pondasi menu lu, nanti kita bisa tambah "Analisis Rute", "Performa Armada", dll
menu = st.sidebar.radio("Pilih Menu:", ["Ringkasan Eksekutif", "Data Raw Operasional"])

st.sidebar.divider()

st.sidebar.header("Filter Laporan")
bulan = st.sidebar.selectbox("Bulan Aktif", ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10"])

# 5. LOGIKA UTAMA & TAMPILAN MENU
query = f'SELECT * FROM "{bulan}"'

try:
    df = pd.read_sql(query, engine)
    
    if menu == "Ringkasan Eksekutif":
        st.subheader(f"Performa Logistik - {bulan}")
        
        # Kartu Metrik
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Order / Surat Jalan", len(df))
        col2.metric("Armada Terpakai", "Sedang dihitung...") # Nanti kita isi logika kontainer di sini
        col3.metric("Status Server", "Online 🟢")
        
        st.info("💡 UI Header udah rapi! Kalau lu buka menu 'Data Raw Operasional' di kiri, tolong cek nama kolom untuk 'Tanggal' dan 'Tipe Mobil/Kontainer' biar kita bisa lanjut bikin grafik distribusinya.")

    elif menu == "Data Raw Operasional":
        st.subheader(f"Database Mentah - {bulan}")
        st.dataframe(df)

except Exception as e:
    st.error(f"Data bulan {bulan} belum tersedia atau koneksi gagal: {e}")
