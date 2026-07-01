import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Konfigurasi Halaman (Wajib paling atas!)
st.set_page_config(page_title="Gotrans TMS Dashboard", page_icon="🚚", layout="wide")

# 2. BUNDLE CSS FUTURISTIK & ELEGAN (Mengubah Background & Style)
st.markdown("""
    <style>
    /* 1. Mengubah background utama web (Deep Tech Gradient) */
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    
    /* 2. Mengubah tampilan Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* 3. Efek Glassmorphism & Neon Glow untuk Kartu Metrik */
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important; /* Border biru neon tipis */
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        transition: transform 0.3s ease, border 0.3s ease;
    }
    
    /* Efek hover pada kartu metrik */
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(56, 189, 248, 0.6) !important;
    }
    
    /* Warna teks Angka Metrik (Biru Cyan Neon) */
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }
    
    /* Warna teks Label Metrik */
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.95rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    /* Merapikan pembatas Divider */
    hr {
        border-color: rgba(56, 189, 248, 0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. HEADER: Logonya Ditengah dan Gedean
# Kita bagi jadi 3 kolom, logo ditaruh di kolom tengah (col_logo) agar presisi di tengah
col_space1, col_logo, col_space2 = st.columns([1.5, 2, 1.5]) 

with col_logo:
    try:
        # Menampilkan logo dengan ukuran proporsional di tengah
        st.image("GoTrans-Postgres/logo_gobel.jpg", use_container_width=True)
    except Exception:
        st.warning("⚠️ Logo 'logo_gobel.jpg' tidak ditemukan di folder GoTrans-Postgres")

# Judul Utama (Centered HTML)
st.markdown("<h1 style='text-align: center; color: #ffffff; font-size: 2.8rem; font-weight: 800; margin-top: 10px; margin-bottom: 0px;'>Gotrans Operational Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #38bdf8; font-size: 1.2rem; letter-spacing: 2px; font-weight: 500;'>LOGISTIK & TRANSPORT MANAGEMENT SYSTEM (TMS)</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 4. SETUP KONEKSI DATABASE
DATABASE_URL = st.secrets["SUPABASE_URL"].strip()
engine = create_engine(DATABASE_URL)

# 5. SIDEBAR NAVIGASI
st.sidebar.markdown("<h2 style='color: #38bdf8;'>NAVIGASI</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Pilih Menu:", ["Ringkasan Eksekutif", "Data Raw Operasional"])

st.sidebar.divider()

st.sidebar.markdown("<h2 style='color: #38bdf8;'>FILTER</h2>", unsafe_allow_html=True)
bulan = st.sidebar.selectbox("Bulan Aktif", ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10"])

# 6. LOGIKA PROSES DATA
query = f'SELECT * FROM "{bulan}"'

try:
    df = pd.read_sql(query, engine)
    
    if menu == "Ringkasan Eksekutif":
        st.markdown(f"### 📈 Ringkasan Finansial Utama — `{bulan}`")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- KALKULASI FINANSIAL INDEX ---
        try:
            rev_col = df.columns[97]          # CT
            cost_col = df.columns[98]         # CU
            rate_vendor_col = df.columns[102] # CY
            add_rate_vendor_col = df.columns[103] # CZ
            
            df[rev_col] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
            df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)
            df[rate_vendor_col] = pd.to_numeric(df[rate_vendor_col], errors='coerce').fillna(0)
            df[add_rate_vendor_col] = pd.to_numeric(df[add_rate_vendor_col], errors='coerce').fillna(0)
            
            df['Final_Cost'] = df[cost_col]
            mask_kosong = df['Final_Cost'] == 0
            df.loc[mask_kosong, 'Final_Cost'] = df.loc[mask_kosong, rate_vendor_col] + df.loc[mask_kosong, add_rate_vendor_col]
            
            total_rev = df[rev_col].sum()
            total_cost = df['Final_Cost'].sum()
            margin_rp = total_rev - total_cost
            
            if total_rev > 0:
                margin_pct = (margin_rp / total_rev) * 100
            else:
                margin_pct = 0
                
            def format_rp(angka):
                if angka >= 1e9:
                    return f"Rp {angka/1e9:.2f} M"
                elif angka >= 1e6:
                    return f"Rp {angka/1e6:.2f} Jt"
                return f"Rp {angka:,.0f}"

            # --- TAMPILAN KARTU METRIK FUTURISTIK ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Revenue", format_rp(total_rev))
            col2.metric("Total Cost", format_rp(total_cost))
            
            delta_color = "normal" if margin_pct >= 0 else "inverse"
            col3.metric("Total Margin", format_rp(margin_rp), f"{margin_pct:.1f}%", delta_color=delta_color)
            col4.metric("Total Surat Jalan", f"{len(df):,}")
            
        except IndexError:
            st.error("⚠️ Struktur data kolom Excel tidak sampai indeks finansial (CT/CU).")

    elif menu == "Data Raw Operasional":
        st.markdown(f"### 🗄️ Database Mentah — `{bulan}`")
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df)

except Exception as e:
    st.error(f"Gagal memuat data atau tabel `{bulan}` belum ada di Supabase: {e}")
