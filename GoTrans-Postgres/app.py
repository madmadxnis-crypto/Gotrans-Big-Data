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
query = f'SELECT * FROM "{bulan}"'

try:
    df = pd.read_sql(query, engine)
    
    if menu == "Ringkasan Eksekutif":
        st.subheader(f"Performa Finansial & Logistik - {bulan}")
        
        # --- BLOK KALKULASI FINANSIAL (Berdasarkan Posisi Kolom Excel) ---
        try:
            # Ambil nama kolom berdasarkan index pastinya
            rev_col = df.columns[97]          # CT
            cost_col = df.columns[98]         # CU
            rate_vendor_col = df.columns[102] # CY
            add_rate_vendor_col = df.columns[103] # CZ
            
            # 1. Bersihkan Data: Pastikan semua terbaca sebagai angka (kalau kosong jadi 0)
            df[rev_col] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
            df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)
            df[rate_vendor_col] = pd.to_numeric(df[rate_vendor_col], errors='coerce').fillna(0)
            df[add_rate_vendor_col] = pd.to_numeric(df[add_rate_vendor_col], errors='coerce').fillna(0)
            
            # 2. Logika Cost (CU vs CY+CZ)
            df['Final_Cost'] = df[cost_col]
            # Deteksi baris yang cost-nya 0 (kosong)
            mask_kosong = df['Final_Cost'] == 0
            # Timpa yang kosong dengan Rate Vendor + Add Rate Vendor
            df.loc[mask_kosong, 'Final_Cost'] = df.loc[mask_kosong, rate_vendor_col] + df.loc[mask_kosong, add_rate_vendor_col]
            
            # 3. Hitung Grand Total
            total_rev = df[rev_col].sum()
            total_cost = df['Final_Cost'].sum()
            margin_rp = total_rev - total_cost
            
            # Hitung persentase aman (anti error dibagi nol)
            if total_rev > 0:
                margin_pct = (margin_rp / total_rev) * 100
            else:
                margin_pct = 0
                
            # Fungsi supaya tampilan Rupiahnya rapi (dalam Miliar / Juta)
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
            
            # Bikin indikator hijau kalau untung, merah kalau rugi
            delta_color = "normal" if margin_pct >= 0 else "inverse"
            col3.metric("Total Margin", format_rp(margin_rp), f"{margin_pct:.1f}%", delta_color=delta_color)
            col4.metric("Total Surat Jalan", len(df))
            
        except IndexError:
            st.error("⚠️ Kolomnya nggak nyampe CT/CU! Pastikan file Excel lu beneran punya format kolom yang panjang.")

    elif menu == "Data Raw Operasional":
        st.subheader(f"Database Mentah - {bulan}")
        st.dataframe(df)

except Exception as e:
    st.error(f"Data bulan {bulan} belum tersedia atau koneksi gagal: {e}")
