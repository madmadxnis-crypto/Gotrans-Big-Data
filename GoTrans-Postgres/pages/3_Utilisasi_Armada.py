import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import datetime
import io

try:
    import holidays
except ImportError:
    st.error("⚠️ Library 'holidays' belum terinstal. Tambahkan 'holidays' di file requirements.txt di GitHub.")
    st.stop()

st.set_page_config(page_title="Utilisasi Armada Pintar", page_icon="🚛", layout="wide")

# --- CSS FUTURISTIK ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important; color: #f8fafc !important; }
    [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.7) !important; backdrop-filter: blur(10px) !important; padding: 20px !important; border-radius: 16px !important; border: 1px solid rgba(56, 189, 248, 0.2) !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important; }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2rem !important; font-weight: 700 !important; }
    hr { border-color: rgba(56, 189, 248, 0.1) !important; }
    .stDownloadButton button { background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; color: white !important; border: none !important; padding: 10px 24px !important; border-radius: 8px !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: left; color: #ffffff; font-weight: 800;'>📊 Report Utilisasi Armada Pintar</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8;'>Filter operasional saling mengunci & otomatis tercetak saat diunduh ke Excel.</p>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# --- KONEKSI & PARSING NAMA TABEL ---
engine = create_engine(st.secrets["SUPABASE_URL"].strip())
try:
    semua_tabel = inspect(engine).get_table_names()
    # Asumsi nama tabel format "Bulan-Tahun" (contoh: Januari-2025)
    tabel_valid = [t for t in semua_tabel if '-' in t]
except Exception:
    tabel_valid = []

if not tabel_valid:
    st.warning("Database belum tersedia atau format nama tabel salah.")
    st.stop()

# Pisahkan Bulan dan Tahun untuk Filter
bulan_set, tahun_set = set(), set()
for t in tabel_valid:
    parts = t.split('-')
    if len(parts) >= 2:
        bulan_set.add(parts[0])
        tahun_set.add(parts[1])

# --- BARIS 1: FILTER DATABASE & TANGGAL ---
col_bln, col_thn, col_start, col_end = st.columns(4)

with col_bln: pilih_bulan = st.selectbox("Bulan:", sorted(list(bulan_set)))
with col_thn: pilih_tahun = st.selectbox("Tahun:", sorted(list(tahun_set), reverse=True))

target_table = f"{pilih_bulan}-{pilih_tahun}"

if target_table not in tabel_valid:
    st.error(f"⚠️ Data untuk {pilih_bulan} {pilih_tahun} belum tersedia di database.")
    st.stop()

# Load Data based on selected month & year
df = pd.read_sql(f'SELECT * FROM "{target_table}"', engine)

# Deteksi Kolom Otomatis
date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date', 'surat_jalan'])), df.columns[0])
branch_col = df.columns[3] if len(df.columns) > 3 else df.columns[0]
client_col = df.columns[12] if len(df.columns) > 12 else df.columns[0]
group_col = df.columns[7] if len(df.columns) > 7 else df.columns[0]
nopol_col = next((c for c in df.columns if 'polisi' in c.lower() or 'nopol' in c.lower()), "No Polisi")
def_col = next((c for c in df.columns if 'definition' in c.lower()), "Definition")
transporter_col = next((c for c in df.columns if 'transporter' in c.lower()), "Nama Transporter")
status_col = next((c for c in df.columns if 'status pengiriman' in c.lower()), "Status Pengiriman")
order_col = next((c for c in df.columns if 'no order' in c.lower() or 'order' in c.lower()), "No Order")
mrc_col = next((c for c in df.columns if 'mrc' in c.lower()), "Total MRC")
rev_col = df.columns[97] if len(df.columns) > 97 else "Revenue"

df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df_valid = df.dropna(subset=[date_col])

min_date = df_valid[date_col].min().date() if not df_valid.empty else datetime.date.today()
max_date = df_valid[date_col].max().date() if not df_valid.empty else datetime.date.today()

with col_start: start_date = st.date_input("Mulai Tanggal:", value=min_date, format="DD/MM/YYYY")
with col_end: end_date = st.date_input("Sampai Tanggal:", value=max_date, format="DD/MM/YYYY")

# --- FILTER DATA AWAL (BERDASARKAN TANGGAL) ---
df_temp = df_valid[(df_valid[date_col].dt.date >= start_date) & (df_valid[date_col].dt.date <= end_date)].copy()

# --- BARIS 2: FILTER SALING MENGUNCI (CASCADING) ---
col_b, col_c, col_g = st.columns(3)

# 1. Branch Filter (Mengunci Client & Group)
with col_b:
    opsi_b = ["Semua"] + sorted(df_temp[branch_col].astype(str).dropna().unique().tolist())
    pilih_branch = st.selectbox("Branch:", opsi_b)
    if pilih_branch != "Semua":
        df_temp = df_temp[df_temp[branch_col].astype(str) == pilih_branch]

# 2. Client Filter (Mengunci Group, setelah Branch dipilih)
with col_c:
    opsi_c = ["Semua"] + sorted(df_temp[client_col].astype(str).dropna().unique().tolist())
    pilih_client = st.selectbox("Client:", opsi_c)
    if pilih_client != "Semua":
        df_temp = df_temp[df_temp[client_col].astype(str) == pilih_client]

# 3. Group Filter (Terkunci oleh Branch dan Client sebelumnya)
with col_g:
    opsi_g = ["Semua"] + sorted(df_temp[group_col].astype(str).dropna().unique().tolist())
    pilih_group = st.selectbox("Group:", opsi_g)
    if pilih_group != "Semua":
        df_temp = df_temp[df_temp[group_col].astype(str) == pilih_group]

# Finalisasi Dataframe Terfilter
df_f = df_temp.copy()

# Filter Khusus Utilisasi (GoTrans & Exclude Cancel)
if transporter_col in df_f.columns:
    df_f = df_f[df_f[transporter_col] == "GoTrans Logistics International"]
if status_col in df_f.columns:
    df_f = df_f[~df_f[status_col].isin(["Cancel Order Approved", "Not Accepted", "Cancel Order Requested"])]


# --- ENGINE LOGIKA HARI KERJA (SLA) ---
id_holidays = holidays.ID(years=range(start_date.year, end_date.year + 1))
cuti_lebaran = set()
for d_obj, name in id_holidays.items():
    if "Idul Fitri" in name or "Lebaran" in name:
        for i in range(-2, 3): cuti_lebaran.add(d_obj + datetime.timedelta(days=i))

hari_kerja = 0
for d in pd.date_range(start_date, end_date):
    d_date = d.date()
    if d.weekday() == 6: continue
    if d_date in cuti_lebaran: continue
    if d_date in id_holidays: continue
    hari_kerja += 1

# --- PIVOT TABLE & AGREGASI ---
st.markdown(f"### 🚛 Hasil Utilisasi (SLA: {hari_kerja} Hari Kerja)")

try:
    df_f[mrc_col] = pd.to_numeric(df_f[mrc_col], errors='coerce').fillna(0)
    df_f[rev_col] = pd.to_numeric(df_f[rev_col], errors='coerce').fillna(0)
    df_f['Work Day'] = hari_kerja
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ritase (Order)", f"{len(df_f):,}")
    c2.metric("Armada Aktif", f"{df_f[nopol_col].nunique()} Unit")
    c3.metric("Total MRC", f"Rp {df_f[mrc_col].sum()/1e6:.1f} Jt")
    c4.metric("Total Revenue", f"Rp {df_f[rev_col].sum()/1e6:.1f} Jt")
    
    pivot_df = df_f.groupby([nopol_col, def_col]).agg(
        Work_Day=('Work Day', 'mean'),
        Ritase=(order_col, 'count'),
        Total_MRC=(mrc_col, 'sum'),
        Total_Revenue=(rev_col, 'sum')
    ).reset_index()
    
    # Simpan versi raw untuk Excel, dan versi format untuk Web
    pivot_excel = pivot_df.copy()
    pivot_df['Total_MRC'] = pivot_df['Total_MRC'].apply(lambda x: f"Rp {x:,.0f}")
    pivot_df['Total_Revenue'] = pivot_df['Total_Revenue'].apply(lambda x: f"Rp {x:,.0f}")
    pivot_df.rename(columns={'Work_Day': 'Work Day'}, inplace=True)
    pivot_excel.rename(columns={'Work_Day': 'Work Day'}, inplace=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.dataframe(pivot_df, use_container_width=True, hide_index=True)
    
    # --- PROSES EXCEL DENGAN HEADER FILTER ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # 1. Buat Header Info Filter
        filter_info = pd.DataFrame({
            'PARAMETER': ['Bulan Database', 'Tahun Database', 'Rentang Tanggal', 'SLA (Hari Kerja)', 'Filter Branch', 'Filter Client', 'Filter Group'],
            'NILAI YANG DIGUNAKAN': [
                pilih_bulan, 
                pilih_tahun, 
                f"{start_date.strftime('%d %B %Y')} s/d {end_date.strftime('%d %B %Y')}", 
                f"{hari_kerja} Hari", 
                pilih_branch, 
                pilih_client, 
                pilih_group
            ]
        })
        
        # 2. Tulis Info Filter di baris paling atas (Mulai dari A1)
        filter_info.to_excel(writer, index=False, sheet_name='PivotUtilisasi', startrow=0, startcol=0)
        
        # 3. Tulis Pivot Data di bawahnya (dikasih jarak 2 baris biar rapi)
        start_row_pivot = len(filter_info) + 2
        pivot_excel.to_excel(writer, index=False, sheet_name='PivotUtilisasi', startrow=start_row_pivot, startcol=0)
    
    st.download_button(
        label="📥 Ekstrak Report & Filter ke Excel",
        data=buffer.getvalue(),
        file_name=f"Utilisasi_Armada_{pilih_bulan}_{pilih_tahun}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except KeyError as e:
    st.error(f"⚠️ Kolom tidak ditemukan di database: {e}")
