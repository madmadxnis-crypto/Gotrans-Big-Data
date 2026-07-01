import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Gotrans TMS Dashboard", page_icon="🚚", layout="wide")

# 2. BUNDLE CSS FUTURISTIK (Simetris & Elegan)
st.markdown("""
    <style>
    /* Background Utama */
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Sidebar Layout */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* KOTAK METRIK: Dipaksa Simetris Sempurna */
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        min-height: 160px !important; /* Memastikan semua kotak tingginya sama persis */
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }
    
    div[data-testid="stMetric"]:hover {
        border: 1px solid rgba(56, 189, 248, 0.6) !important;
    }
    
    /* Nilai Angka */
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }
    
    /* Label Judul Kotak */
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    hr {
        border-color: rgba(56, 189, 248, 0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. HEADER: Logo Tengah & Gedean
col_space1, col_logo, col_space2 = st.columns([1.5, 2, 1.5]) 
with col_logo:
    try:
        st.image("GoTrans-Postgres/logo_gobel.jpg", use_container_width=True)
    except Exception:
        st.warning("⚠️ Logo 'logo_gobel.jpg' tidak ditemukan di folder GoTrans-Postgres")

st.markdown("<h1 style='text-align: center; color: #ffffff; font-size: 2.5rem; font-weight: 800; margin-top: 10px; margin-bottom: 0px;'>Gotrans Operational Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #38bdf8; font-size: 1.1rem; letter-spacing: 2px; font-weight: 500;'>LOGISTIK & TRANSPORT MANAGEMENT SYSTEM (TMS)</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 4. KONEKSI DATABASE
DATABASE_URL = st.secrets["SUPABASE_URL"].strip()
engine = create_engine(DATABASE_URL)

# 5. SIDEBAR CONTROL
st.sidebar.markdown("<h2 style='color: #38bdf8;'>NAVIGASI</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Pilih Menu:", ["Ringkasan Eksekutif", "Data Raw Operasional"])

st.sidebar.divider()

st.sidebar.markdown("<h2 style='color: #38bdf8;'>FILTER BULAN</h2>", unsafe_allow_html=True)
bulan = st.sidebar.selectbox("Bulan Aktif", ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10"])

# 6. ENGINE PROSES UTAMA
query = f'SELECT * FROM "{bulan}"'

try:
    df = pd.read_sql(query, engine)
    
    # --- AUTOMATIC DATE COLUMN DETECTION ---
    date_col = None
    for col in df.columns:
        if any(k in col.lower() for k in ['tanggal', 'tgl', 'date', 'surat_jalan', 'sj']):
            date_col = col
            break
    if not date_col:
        date_col = df.columns[0] # Fallback ke kolom pertama jika tidak terdeteksi
    
    # Konversi kolom tanggal ke format datetime resmi Python
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col]) # Buang baris yang tanggalnya rusak
    
    # Dapatkan tanggal terkecil dan terbesar di bulan tersebut secara otomatis
    min_date = df[date_col].min().date()
    max_date = df[date_col].max().date()
    
    # Tambahkan komponen Filter Ganti Tanggal Interaktif di Sidebar
    st.sidebar.divider()
    st.sidebar.markdown("<h2 style='color: #38bdf8;'>FILTER TANGGAL</h2>", unsafe_allow_html=True)
    start_date, end_date = st.sidebar.date_input(
        "Rentang Tanggal:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Potong data frame berdasarkan filter tanggal yang dipilih
    df_filtered = df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)].copy()
    df_filtered = df_filtered.sort_values(by=date_col)

    # --- JALUR MENU 1: RINGKASAN EKSEKUTIF ---
    if menu == "Ringkasan Eksekutif":
        st.markdown(f"### 📈 Ringkasan Finansial Utama ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')})")
        st.markdown("<br>", unsafe_allow_html=True)
        
        try:
            # Ambil indeks kolom finansial lu (CT, CU, CY, CZ)
            rev_col = df_filtered.columns[97]          
            cost_col = df_filtered.columns[98]         
            rate_vendor_col = df_filtered.columns[102] 
            add_rate_vendor_col = df_filtered.columns[103] 
            
            # Bersihkan tipe data biar beneran jadi angka matematis
            df_filtered[rev_col] = pd.to_numeric(df_filtered[rev_col], errors='coerce').fillna(0)
            df_filtered[cost_col] = pd.to_numeric(df_filtered[cost_col], errors='coerce').fillna(0)
            df_filtered[rate_vendor_col] = pd.to_numeric(df_filtered[rate_vendor_col], errors='coerce').fillna(0)
            df_filtered[add_rate_vendor_col] = pd.to_numeric(df_filtered[add_rate_vendor_col], errors='coerce').fillna(0)
            
            # Terapkan Logika Substitusi Cost Kosong
            df_filtered['Final_Cost'] = df_filtered[cost_col]
            mask_kosong = df_filtered['Final_Cost'] == 0
            df_filtered.loc[mask_kosong, 'Final_Cost'] = df_filtered.loc[mask_kosong, rate_vendor_col] + df_filtered.loc[mask_kosong, add_rate_vendor_col]
            
            # Hitung Margin Bersih per baris
            df_filtered['Calculated_Margin'] = df_filtered[rev_col] - df_filtered['Final_Cost']
            
            # Hitung Total Keseluruhan
            total_rev = df_filtered[rev_col].sum()
            total_cost = df_filtered['Final_Cost'].sum()
            margin_rp = total_rev - total_cost
            margin_pct = (margin_rp / total_rev * 100) if total_rev > 0 else 0
                
            def format_rp(angka):
                if angka >= 1e9: return f"Rp {angka/1e9:.2f} M"
                elif angka >= 1e6: return f"Rp {angka/1e6:.2f} Jt"
                return f"Rp {angka:,.0f}"

            # --- DISPLAY KOTAK METRIK (Symmetrical Style) ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Revenue", format_rp(total_rev))
            col2.metric("Total Cost", format_rp(total_cost))
            
            delta_color = "normal" if margin_pct >= 0 else "inverse"
            col3.metric("Total Margin", format_rp(margin_rp), f"{margin_pct:.1f}%", delta_color=delta_color)
            col4.metric("Total Surat Jalan", f"{len(df_filtered):,}")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("### 📊 Tren Performa Operasional Harian")
            
            # --- PREPARASI DATA GRAFIK HARIAN ---
            # Kelompokkan data berdasarkan tanggal murni (YMD)
            df_daily = df_filtered.groupby(df_filtered[date_col].dt.date).agg({
                rev_col: 'sum',
                'Final_Cost': 'sum',
                'Calculated_Margin': 'sum'
            }).reset_index()
            
            df_daily.columns = ['Tanggal', 'Revenue', 'Cost', 'Margin']
            
            # MEMBUAT DUA GRAFIK LINE BERDAMPINGAN (Command Center Look)
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Grafik 1: Revenue vs Cost
                fig_rev_cost = px.line(
                    df_daily, x='Tanggal', y=['Revenue', 'Cost'],
                    labels={'value': 'Jumlah Angka (Rp)', 'variable': 'Komponen'},
                    title="Tren Harian: Total Revenue vs Total Cost",
                    template="plotly_dark",
                    color_discrete_sequence=["#38bdf8", "#f43f5e"] # Warna Cyan & Rose Neon
                )
                fig_rev_cost.update_layout(
                    paper_bgcolor='rgba(17, 24, 39, 0.5)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig_rev_cost, use_container_width=True)
                
            with chart_col2:
                # Grafik 2: Margin Mandiri
                fig_margin = px.line(
                    df_daily, x='Tanggal', y='Margin',
                    labels={'Margin': 'Total Margin (Rp)'},
                    title="Tren Harian: Pergerakan Net Margin",
                    template="plotly_dark",
                    color_discrete_sequence=["#10b981"] # Warna Emerald Green Neon
                )
                fig_margin.update_layout(
                    paper_bgcolor='rgba(17, 24, 39, 0.5)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig_margin, use_container_width=True)
            
        except IndexError:
            st.error("⚠️ Struktur data kolom Excel berubah atau posisi indeks tidak sesuai.")

    # --- JALUR MENU 2: DATA RAW OPERASIONAL ---
    elif menu == "Data Raw Operasional":
        st.markdown(f"### 🗄️ Database Mentah Terfilter — `{bulan}`")
        st.markdown(f"Menampilkan data dari tanggal {start_date} sampai {end_date}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"Gagal memuat data atau tabel `{bulan}` belum ada di Supabase: {e}")
