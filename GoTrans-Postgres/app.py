import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.express as px
import datetime
import io

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Gotrans TMS Dashboard", page_icon="Email-Signature-GLI.ico", layout="wide")

# 2. BUNDLE CSS FUTURISTIK & CUSTOM SIDEBAR EASYGO STYLE
st.markdown("""
    <style>
    /* Tema Dasar */
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Custom Sidebar mirip EASYGO */
    [data-testid="stSidebar"] {
        background-color: #1f2336 !important; /* Warna dark blue EasyGo */
        border-right: 1px solid #2d3248 !important;
    }
    .easygo-menu {
        font-family: 'Inter', sans-serif;
        color: #a0a5b1;
        font-size: 0.95rem;
        line-height: 2.2;
        cursor: pointer;
    }
    .easygo-menu-active {
        color: #ffffff;
        font-weight: 600;
        background-color: #38bdf820;
        padding-left: 10px;
        border-left: 3px solid #38bdf8;
        border-radius: 4px;
    }
    .easygo-indent-1 { padding-left: 20px; }
    .easygo-indent-2 { padding-left: 40px; font-size: 0.85rem;}
    
    /* Metrik Card */
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    
    /* Label Filter Custom */
    .filter-label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        margin-bottom: -15px !important;
        font-weight: 500 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. KONEKSI DATABASE
DATABASE_URL = st.secrets["SUPABASE_URL"].strip()
engine = create_engine(DATABASE_URL)

# ==========================================
# 4. SIDEBAR NAVIGATION (EASYGO STYLE)
# ==========================================
st.sidebar.markdown("<h2 style='color: #ffffff; font-weight: 800; text-align: center;'>EASYGO <span style='font-size: 0.8rem; font-weight: 300; color: #38bdf8;'>TMS</span></h2>", unsafe_allow_html=True)
st.sidebar.divider()

# Tampilan Menu Statis (Bisa diubah jadi tombol/radio jika ingin difungsikan multi-page)
st.sidebar.markdown("""
<div class='easygo-menu'>🏠 Dashboard</div>
<div class='easygo-menu'>📍 Real Monitoring</div>
<div class='easygo-menu'>📂 Master</div>
<div class='easygo-menu'>⚙️ Advance</div>
<div class='easygo-menu'>📦 Order Management</div>
<div class='easygo-menu'>📉 Report</div>
<div class='easygo-menu easygo-indent-1'>• Safety Report</div>
<div class='easygo-menu easygo-indent-1'>• Operational</div>
<div class='easygo-menu easygo-indent-1'>▾ Trip History</div>
<div class='easygo-menu easygo-indent-2'>Detail Report</div>
<div class='easygo-menu easygo-indent-2'>Summary Report</div>
<div class='easygo-menu easygo-indent-2'>Monthly Report</div>
<div class='easygo-menu easygo-indent-2'>Monthly Update Unit</div>
<div class='easygo-menu easygo-indent-2'>Parking Trip DO</div>
<div class='easygo-menu easygo-indent-2'>Report Start Stop Trip</div>
<div class='easygo-menu easygo-indent-2 easygo-menu-active'>Mileage Report</div>
<div class='easygo-menu'>🚚 Delivery Order</div>
""", unsafe_allow_html=True)


# ==========================================
# 5. HEADER UTAMA
# ==========================================
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown("<h1 style='color: #ffffff; font-size: 2.2rem; margin-bottom: 0px;'>📝 Utilisasi Armada Dashboard 📝</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 1rem;'>Otomatis mendeteksi Hari Kerja</p>", unsafe_allow_html=True)
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("🏠 Kembali ke Home", use_container_width=True)

st.divider()

# ==========================================
# 6. FILTER OPERASIONAL (GAYA UTILISASI ARMADA)
# ==========================================
# Baris 1: Filter Waktu & Tanggal
c1, c2, c3, c4, c5 = st.columns(5)
with c1: filter_waktu = st.selectbox("Filter Waktu:", ["Bulan", "Harian"])
with c2: val_bulan = st.selectbox("Bulan:", [f"{i:02d}" for i in range(1, 13)], index=datetime.datetime.now().month - 1)
with c3: val_tahun = st.selectbox("Tahun:", [str(y) for y in range(2024, 2028)], index=2) # Default 2026
with c4: mulai_tgl = st.date_input("Mulai Tanggal:")
with c5: sampai_tgl = st.date_input("Sampai Tanggal:")

# Nama tabel dinamis berdasarkan filter Bulan & Tahun di atas (Bukan dari Sidebar lagi)
tabel_aktif = f"{val_tahun}-{val_bulan}"

# Proses Tarik Data Base untuk Opsi Filter
df = pd.DataFrame()
opsi_branch, opsi_client, opsi_group, opsi_tipe, opsi_nopol = ["Semua"], ["Semua"], ["Semua"], ["bisa pilih banyak tipe"], ["bisa pilih banyak Nopol"]

try:
    query = f'SELECT * FROM "{tabel_aktif}"'
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        # Deteksi Kolom Otomatis
        date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date'])), df.columns[0])
        branch_col = df.columns[3] if len(df.columns) > 3 else df.columns[0]
        client_col = df.columns[12] if len(df.columns) > 12 else df.columns[0]
        group_col = next((c for c in df.columns if 'group' in c.lower()), df.columns[7] if len(df.columns) > 7 else df.columns[0])
        
        # Deteksi Kolom Truk & Nopol
        tipe_col = next((c for c in df.columns if 'tipe_truk' in c.lower() or 'type' in c.lower()), df.columns[33] if len(df.columns) > 33 else df.columns[0])
        nopol_col = next((c for c in df.columns if 'polisi' in c.lower() or 'plat' in c.lower()), df.columns[32] if len(df.columns) > 32 else df.columns[0])

        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df_valid = df.dropna(subset=[date_col])
        
        # Update Opsi Filter
        if not df_valid.empty:
            opsi_branch += sorted(df_valid[branch_col].dropna().unique().tolist())
            opsi_client += sorted(df_valid[client_col].dropna().unique().tolist())
            opsi_group += sorted(df_valid[group_col].dropna().unique().tolist())
            opsi_tipe += sorted(df_valid[tipe_col].dropna().unique().tolist())
            opsi_nopol += sorted(df_valid[nopol_col].dropna().unique().tolist())
except Exception:
    st.warning(f"⚠️ Data untuk periode {tabel_aktif} belum tersedia di database.")

# Baris 2: Atribut Logistik
c6, c7, c8, c9 = st.columns(4)
with c6: transporter = st.selectbox("Transporter:", ["GoTrans Logistics International", "Lainnya"])
with c7: branch = st.selectbox("Branch:", opsi_branch)
with c8: client = st.selectbox("Client:", opsi_client)
with c9: group = st.selectbox("Group:", opsi_group)

# Baris 3: Armada
c10, c11 = st.columns(2)
with c10: type_mobil = st.multiselect("Type Mobil:", opsi_tipe, default=opsi_tipe[0] if opsi_tipe else None)
with c11: no_polisi = st.multiselect("No Polisi :", opsi_nopol, default=opsi_nopol[0] if opsi_nopol else None)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 7. ENGINE PROSES & RENDER METRIK
# ==========================================
if not df.empty and 'df_valid' in locals() and not df_valid.empty:
    # 1. Filter Tanggal (Range Input Utama)
    df_filtered = df_valid[(df_valid[date_col].dt.date >= mulai_tgl) & (df_valid[date_col].dt.date <= sampai_tgl)].copy()
    
    # 2. Filter Dropdown Operasional
    if branch != "Semua": df_filtered = df_filtered[df_filtered[branch_col] == branch]
    if client != "Semua": df_filtered = df_filtered[df_filtered[client_col] == client]
    if group != "Semua": df_filtered = df_filtered[df_filtered[group_col] == group]
    
    # Filter Multiselect
    if type_mobil and "bisa pilih banyak tipe" not in type_mobil: 
        df_filtered = df_filtered[df_filtered[tipe_col].isin(type_mobil)]
    if no_polisi and "bisa pilih banyak Nopol" not in no_polisi: 
        df_filtered = df_filtered[df_filtered[nopol_col].isin(no_polisi)]

    st.markdown("### 🚚 Utilisasi (SLA: 2 Hari Kerja)")
    
    # Kalkulasi Metrik (Diadaptasi dari kode lama yang sudah fix)
    try:
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
        
        total_rev = df_filtered[rev_col].sum()
        total_cost = df_filtered['Final_Cost'].sum()
        total_so = len(df_filtered)
        
        # Hitung Armada Aktif Unik
        armada_aktif = df_filtered[nopol_col].nunique() if not df_filtered.empty else 0
        
        def format_rp(angka):
            if angka >= 1e9: return f"Rp {angka/1e9:.1f} M"
            elif angka >= 1e6: return f"Rp {angka/1e6:.1f} Jt"
            return f"Rp {angka:,.0f}"

        # Render 4 Kotak Metrik
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Ritase (Sales Order)", f"{total_so}")
        m2.metric("Armada Aktif", f"{armada_aktif} Unit")
        m3.metric("Total MRC (Cost)", format_rp(total_cost))
        m4.metric("Total Revenue", format_rp(total_rev))
        
        # Tombol Download Excel
        st.markdown("<br>", unsafe_allow_html=True)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export = df_filtered.copy()
            df_export[date_col] = df_export[date_col].dt.strftime('%Y-%m-%d')
            df_export.to_excel(writer, index=False, sheet_name='Data_Utilisasi')
            
        st.download_button(
            label="📥 Unduh Data Utilisasi (Excel)",
            data=buffer.getvalue(),
            file_name=f"Utilisasi_{tabel_aktif}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except IndexError:
         st.error("⚠️ Struktur data berubah, pastikan kolom Excel sesuai dengan format database.")
