import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.express as px
import datetime
import io # Wajib diimport untuk fitur unduh Excel

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Gotrans TMS Dashboard", page_icon="🚜", layout="wide")

# 2. BUNDLE CSS FUTURISTIK & ELEGAN
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b !important;
    }
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        min-height: 160px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }
    div[data-testid="stMetric"]:hover {
        border: 1px solid rgba(56, 189, 248, 0.6) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    hr {
        border-color: rgba(56, 189, 248, 0.1) !important;
    }
    div[data-testid="stDateInput"] {
        margin-top: 5px !important;
    }
    /* Style khusus tombol download Excel biar futuristik */
    .stDownloadButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(16, 185, 129, 0.5) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. HEADER
col_space1, col_logo, col_space2 = st.columns([1.5, 2, 1.5]) 
with col_logo:
    try:
        st.image("GoTrans-Postgres/logo_gobel.jpg", use_container_width=True)
    except Exception:
        st.warning("⚠️ Logo 'logo_gobel.jpg' tidak ditemukan.")

st.markdown("<h1 style='text-align: center; color: #ffffff; font-size: 2.5rem; font-weight: 800; margin-top: 10px; margin-bottom: 0px;'>Gotrans Operational Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #38bdf8; font-size: 1.1rem; letter-spacing: 2px; font-weight: 500;'>TRANSPORT MANAGEMENT SYSTEM (TMS)</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 4. KONEKSI DATABASE
DATABASE_URL = st.secrets["SUPABASE_URL"].strip()
engine = create_engine(DATABASE_URL)

# 5. SIDEBAR CONTROL
st.sidebar.markdown("<h2 style='color: #38bdf8;'>NAVIGASI</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Pilih Menu:", ["Ringkasan Eksekutif", "Data Raw Operasional"])

st.sidebar.divider()

try:
    inspector = inspect(engine)
    semua_tabel = inspector.get_table_names()
    daftar_bulan = sorted([t for t in semua_tabel if '-' in t], reverse=True)
except Exception:
    daftar_bulan = ["Gagal membaca database"]

if not daftar_bulan:
    daftar_bulan = ["Data Belum Tersedia"]

st.sidebar.markdown("<h2 style='color: #38bdf8;'>FILTER BULAN</h2>", unsafe_allow_html=True)
bulan = st.sidebar.selectbox("Bulan Aktif", daftar_bulan)

# 6. ENGINE PROSES UTAMA
if bulan not in ["Gagal membaca database", "Data Belum Tersedia"]:
    query = f'SELECT * FROM "{bulan}"'

    try:
        df = pd.read_sql(query, engine)
        # --- DETEKSI KOLOM OTOMATIS MENGHINDARI INDEX ERROR ---
        date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date', 'surat_jalan'])), df.columns[0])
        branch_col = df.columns[3]   # Kolom D (Index 3)
        client_col = df.columns[12]  # Kolom M (Index 12)
        group_col = df.columns[7]    # Kolom H (Index 7) - FIXED
        
        # Deteksi otomatis untuk kolom Group
        group_col = next((c for c in df.columns if 'group' in c.lower()), None)
        if not group_col:
            group_col = df.columns[13] if len(df.columns) > 13 else client_col

        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df_valid = df.dropna(subset=[date_col])
        
        if df_valid.empty:
            min_date, max_date = datetime.date.today(), datetime.date.today()
        else:
            min_date, max_date = df_valid[date_col].min().date(), df_valid[date_col].max().date()
            
        start_date, end_date = min_date, max_date

        # --- BARIS JUDUL & FILTER TANGGAL SEJAJAR ---
        col_judul, col_filter = st.columns([2.5, 1.5]) 
        
        with col_judul:
            if menu == "Ringkasan Eksekutif":
                st.markdown(f"### 📈 Revenue")
            elif menu == "Data Raw Operasional":
                st.markdown(f"### 🗄️ Database Mentah Terfilter")

        with col_filter:
            if not df_valid.empty:
                date_range = st.date_input("Rentang Analisis:", value=(min_date, max_date), min_value=min_date, max_value=max_date, label_visibility="collapsed")
                if isinstance(date_range, tuple):
                    start_date = date_range[0]
                    end_date = date_range[1] if len(date_range) > 1 else date_range[0]
                else:
                    start_date = date_range
                    end_date = date_range

        # Saringan Awal: Rentang Tanggal
        if not df_valid.empty:
            df_filtered = df_valid[(df_valid[date_col].dt.date >= start_date) & (df_valid[date_col].dt.date <= end_date)].copy()
        else:
            df_filtered = df.copy()

        # --- BARIS FILTER OPERASIONAL BARU (BRANCH, CLIENT, GROUP) ---
        st.markdown("<p style='color: #38bdf8; font-weight: 600; margin-bottom: 5px;'>Filter Operasional Lapangan:</p>", unsafe_allow_html=True)
        col_b, col_c, col_g = st.columns(3)
        
        with col_b:
            opsi_branch = ["Semua"] + sorted(df_filtered[branch_col].dropna().unique().tolist())
            pilih_branch = st.selectbox("Branch:", opsi_branch)
        with col_c:
            opsi_client = ["Semua"] + sorted(df_filtered[client_col].dropna().unique().tolist())
            pilih_client = st.selectbox("Client:", opsi_client)
        with col_g:
            opsi_group = ["Semua"] + sorted(df_filtered[group_col].dropna().unique().tolist())
            pilih_group = st.selectbox("Group:", opsi_group)

        # Terapkan Saringan Operasional ke Dataframe
        if pilih_branch != "Semua":
            df_filtered = df_filtered[df_filtered[branch_col] == pilih_branch]
        if pilih_client != "Semua":
            df_filtered = df_filtered[df_filtered[client_col] == pilih_client]
        if pilih_group != "Semua":
            df_filtered = df_filtered[df_filtered[group_col] == pilih_group]

        df_filtered = df_filtered.sort_values(by=date_col)
            
        st.markdown(f"<p style='color: #94a3b8; font-size: 0.95rem; margin-top: -5px;'>Periode Aktif: {start_date.strftime('%d %b %Y')} s/d {end_date.strftime('%d %b %Y')} | Filter: Branch ({pilih_branch}), Client ({pilih_client}), Group ({pilih_group})</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # --- MENU 1: RINGKASAN EKSEKUTIF ---
        if menu == "Ringkasan Eksekutif":
            try:
                # Indeks Finansial Tetap Sama
                rev_col = df_filtered.columns[97]          
                cost_col = df_filtered.columns[98]         
                rate_vendor_col = df_filtered.columns[102] 
                add_rate_vendor_col = df_filtered.columns[103] 
                
                df_filtered[rev_col] = pd.to_numeric(df_filtered[rev_col], errors='coerce').fillna(0)
                df_filtered[cost_col] = pd.to_numeric(df_filtered[cost_col], errors='coerce').fillna(0)
                df_filtered[rate_vendor_col] = pd.to_numeric(df_filtered[rate_vendor_col], errors='coerce').fillna(0)
                df_filtered[add_rate_vendor_col] = pd.to_numeric(df_filtered[add_rate_vendor_col], errors='coerce').fillna(0)
                
                df_filtered['Final_Cost'] = df_filtered[cost_col]
                mask_kosong = df_filtered['Final_Cost'] == 0
                df_filtered.loc[mask_kosong, 'Final_Cost'] = df_filtered.loc[mask_kosong, rate_vendor_col] + df_filtered.loc[mask_kosong, add_rate_vendor_col]
                
                df_filtered['Calculated_Margin'] = df_filtered[rev_col] - df_filtered['Final_Cost']
                
                total_rev = df_filtered[rev_col].sum()
                total_cost = df_filtered['Final_Cost'].sum()
                margin_rp = total_rev - total_cost
                margin_pct = (margin_rp / total_rev * 100) if total_rev > 0 else 0
                    
                def format_rp(angka):
                    if angka >= 1e9: return f"Rp {angka/1e9:.2f} M"
                    elif angka >= 1e6: return f"Rp {angka/1e6:.2f} Jt"
                    return f"Rp {angka:,.0f}"

                # Tampilan Kotak Metrik Simetris
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Revenue", format_rp(total_rev))
                col2.metric("Total Cost", format_rp(total_cost))
                
                delta_color = "normal" if margin_pct >= 0 else "inverse"
                col3.metric("Total Margin", format_rp(margin_rp), f"{margin_pct:.1f}%", delta_color=delta_color)
                col4.metric("Total Sales Order", f"{len(df_filtered):,}")
                
                # --- TOMBOL EKSTRAK EXCEL (Sesuai Tampilan Layar Utama) ---
                st.markdown("<br>", unsafe_allow_html=True)
                col_btn, _ = st.columns([1, 3])
                with col_btn:
                    try:
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_export = df_filtered.copy()
                            # Ubah format datetime tanggal jadi string teks bersih khusus buat file Excel
                            df_export[date_col] = df_export[date_col].dt.strftime('%Y-%m-%d')
                            df_export.to_excel(writer, index=False, sheet_name='TMS_Filtered')
                        
                        st.download_button(
                            label="📥 Ekstrak Data ke Excel",
                            data=buffer.getvalue(),
                            file_name=f"Gotrans_Ekstrak_{bulan}_{start_date}_to_{end_date}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as ex:
                        st.error(f"Gagal memproses ekstrak Excel: {ex}")

                # Grafik Tren Harian
                if not df_valid.empty and not df_filtered.empty:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown("### 📊 Tren Performa Operasional Harian")
                    
                    df_daily = df_filtered.groupby(df_filtered[date_col].dt.date).agg({
                        rev_col: 'sum',
                        'Final_Cost': 'sum',
                        'Calculated_Margin': 'sum'
                    }).reset_index()
                    
                    df_daily.columns = ['Tanggal', 'Revenue', 'Cost', 'Margin']
                    
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        fig_rev_cost = px.line(
                            df_daily, x='Tanggal', y=['Revenue', 'Cost'],
                            labels={'value': 'Jumlah Angka (Rp)', 'variable': 'Komponen'},
                            title="Tren Harian: Total Revenue vs Total Cost",
                            template="plotly_dark",
                            color_discrete_sequence=["#38bdf8", "#f43f5e"] 
                        )
                        fig_rev_cost.update_layout(
                            paper_bgcolor='rgba(17, 24, 39, 0.5)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                        )
                        st.plotly_chart(fig_rev_cost, use_container_width=True)
                        
                    with chart_col2:
                        fig_margin = px.line(
                            df_daily, x='Tanggal', y='Margin',
                            labels={'Margin': 'Total Margin (Rp)'},
                            title="Tren Harian: Pergerakan Net Margin",
                            template="plotly_dark",
                            color_discrete_sequence=["#10b981"] 
                        )
                        fig_margin.update_layout(
                            paper_bgcolor='rgba(17, 24, 39, 0.5)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                        )
                        st.plotly_chart(fig_margin, use_container_width=True)
                
            except IndexError:
                st.error("⚠️ Struktur data kolom Excel berubah atau posisi indeks tidak sesuai.")

        # --- MENU 2: DATA RAW OPERASIONAL ---
        elif menu == "Data Raw Operasional":
            st.dataframe(df_filtered)

    except Exception as e:
        st.error(f"Gagal memuat data dari tabel `{bulan}`: {e}")
