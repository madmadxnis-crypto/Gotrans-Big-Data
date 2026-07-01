import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Konfigurasi Halaman (Wajib paling atas!)
st.set_page_config(page_title="Gotrans TMS Dashboard", page_icon="🚚", layout="wide")

# 2. HEADER: Logo dan Judul berdampingan
col_logo, col_judul = st.columns([1, 4]) # Rasio lebar kolom 1:4

# 2. HEADER: Logo dan Judul berdampingan
col_logo, col_judul = st.columns([1, 4]) # Rasio lebar kolom 1:4

with col_logo:
    try:
        # Mencoba menampilkan logo
        st.image("GoTrans-Postgres/logo_gobel.jpg", use_container_width=True)
    except Exception:
        # Kalau gambar nggak ketemu, lewati saja biar aplikasi nggak mati
        st.warning("Logo hilang")

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
# 5. LOGIKA UTAMA & TAMPILAN MENU
query = f'SELECT * FROM "{bulan}"'

try:
    df = pd.read_sql(query, engine)
    
    if menu == "Ringkasan Eksekutif":
        st.subheader(f"Performa Finansial & Logistik - {bulan}")
        
        # --- BLOK KALKULASI FINANSIAL (PENTING: Ganti nama kolom sesuai data aslimu!) ---
        # Contoh: asumsikan lu punya kolom 'Total_Revenue' dan 'Total_Cost'
        # Jika nama kolom beda, WAJIB diganti di bawah ini.
        try:
            total_rev = df['Total_Revenue'].sum()
            total_cost = df['Total_Cost'].sum()
            margin_rp = total_rev - total_cost
            
            # Hindari pembagian dengan nol
            if total_rev > 0:
                margin_pct = (margin_rp / total_rev) * 100
            else:
                margin_pct = 0
                
            # Format ke Rupiah (Miliar/Juta biar rapi)
            def format_rp(angka):
                if angka >= 1e9:
                    return f"Rp {angka/1e9:.2f} M"
                elif angka >= 1e6:
                    return f"Rp {angka/1e6:.2f} Jt"
                return f"Rp {angka:,.0f}"

            # --- TAMPILAN KARTU METRIK ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Revenue", format_rp(total_rev))
            col2.metric("Total Cost", format_rp(total_cost))
            
            # Bikin warna hijau kalau margin positif, merah kalau negatif
            delta_color = "normal" if margin_pct >= 0 else "inverse"
            col3.metric("Margin", format_rp(margin_rp), f"{margin_pct:.1f}%", delta_color=delta_color)
            col4.metric("Total Order", len(df))
            
        except KeyError:
            st.error("⚠️ Kolom finansial tidak ditemukan! Pastikan data lu punya kolom 'Total_Revenue' dan 'Total_Cost', lalu ubah namanya di kode.")
            st.info("Buka menu 'Data Raw Operasional' untuk mengecek nama asli kolomnya.")

    elif menu == "Data Raw Operasional":
        st.subheader(f"Database Mentah - {bulan}")
        st.dataframe(df)

except Exception as e:
    st.error(f"Data bulan {bulan} belum tersedia atau koneksi gagal: {e}")
