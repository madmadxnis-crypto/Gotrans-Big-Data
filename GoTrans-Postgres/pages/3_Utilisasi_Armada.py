import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import datetime
import io

# Wajib install library 'holidays' di requirements.txt!
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
    /* Mematikan sidebar default agar layar penuh */
    [data-testid="stSidebar"] { display: none !important; }
    
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.7) !important; backdrop-filter: blur(10px) !important; padding: 20px !important; border-radius: 16px !important; border: 1px solid rgba(56, 189, 248, 0.2) !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important; }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2rem !important; font-weight: 700 !important; }
    hr { border-color: rgba(56, 189, 248, 0.1) !important; }
    div[data-testid="stDateInput"] { margin-top: 5px !important; }
    
    /* Tombol Download Excel */
    .stDownloadButton button { background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; color: white !important; border: none !important; padding: 10px 24px !important; border-radius: 8px !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: left; color: #ffffff; font-weight: 800;'>📊 Report Utilisasi Armada Pintar</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8;'>Sistem otomatis mendeteksi Hari Kerja, SLA, dan Utilisasi Ritase per Kendaraan.</p>", unsafe_allow_html=True)

# --- KONEKSI DATABASE ---
engine = create_engine(st.secrets["SUPABASE_URL"].strip())
try:
    semua_tabel = inspect(engine).get_table_names()
    daftar_bulan = sorted([t for t in semua_tabel if '-' in t], reverse=True)
except Exception:
    daftar_bulan = ["Data Belum Tersedia"]

# --- BARIS FILTER ATAS (FULL IN-PAGE) ---
st.markdown("<hr style='margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# Membagi layar jadi 6 kolom untuk filter sejajar
col_db, col_days, col_date, col_branch, col_client, col_group = st.columns([1, 1, 1.5, 1, 1, 1])

with col_db:
    bulan = st.selectbox("Database (Bulan):", daftar_bulan)

# Stop proses kalau database kosong
if bulan == "Data Belum Tersedia":
    st.warning("Database belum tersedia.")
    st.stop()

df = pd.read_sql(f'SELECT * FROM "{bulan}"', engine)

# --- DETEKSI KOLOM OTOMATIS ---
date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date', 'surat_jalan'])), df.columns[0])
branch_col = df.columns[3] if len(df.columns) > 3 else df.columns[0]
client_col = df.columns[12] if len(df.columns) > 12 else df.columns[0]
group_col = df.columns[7] if len(df.columns) > 7 else df.columns[0]

# Kolom Spesifik Utilisasi Armada (Dari VBA)
nopol_col = next((c for c in df.columns if 'polisi' in c.lower() or 'nopol' in c.lower()), "No Polisi")
def_col = next((c for c in df.columns if 'definition' in c.lower()), "Definition")
transporter_col = next((c for c in df.columns if 'transporter' in c.lower()), "Nama Transporter")
status_col = next((c for c in df.columns if 'status pengiriman' in c.lower()), "Status Pengiriman")
order_col = next((c for c in df.columns if 'no order' in c.lower() or 'order' in c.lower()), "No Order")
mrc_col = next((c for c in df.columns if 'mrc' in c.lower()), "Total MRC")
rev_col = df.columns[97] if len(df.columns) > 97 else "Revenue" # CT column

df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df_valid = df.dropna(subset=[date_col])

min_date = df_valid[date_col].min().date() if not df_valid.empty else datetime.date.today()
max_date = df_valid[date_col].max().date() if not df_valid.empty else datetime.date.today()

with col_days:
    opsi_hari = ["Semua", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    pilih_hari = st.selectbox("Days (Hari):", opsi_hari)

with col_date:
    date_range = st.date_input("Rentang Analisis:", value=(min_date, max_date), format="DD/MM/YYYY")
    if isinstance(date_range, (list, tuple)):
        start_date = date_range[0]
        end_date = date_range[1] if len(date_range) > 1 else date_range[0]
    else:
        start_date = end_date = date_range

# Saringan Teks Otomatis
opsi_b = ["Semua"] + sorted(df_valid[branch_col].astype(str).dropna().unique().tolist())
opsi_c = ["Semua"] + sorted(df_valid[client_col].astype(str).dropna().unique().tolist())
opsi_g = ["Semua"] + sorted(df_valid[group_col].astype(str).dropna().unique().tolist())

with col_branch: pilih_branch = st.selectbox("Branch:", opsi_b)
with col_client: pilih_client = st.selectbox("Client:", opsi_c)
with col_group: pilih_group = st.selectbox("Group:", opsi_g)

# --- TERAPKAN FILTER KE DATAFRAME ---
df_f = df_valid[(df_valid[date_col].dt.date >= start_date) & (df_valid[date_col].dt.date <= end_date)].copy()

# Filter Days (Nama Hari)
if pilih_hari != "Semua":
    # Pandas dayofweek: 0=Senin, 1=Selasa, ..., 6=Minggu
    map_hari = {"Senin": 0, "Selasa": 1, "Rabu": 2, "Kamis": 3, "Jumat": 4, "Sabtu": 5, "Minggu": 6}
    df_f = df_f[df_f[date_col].dt.dayofweek == map_hari[pilih_hari]]

if pilih_branch != "Semua": df_f = df_f[df_f[branch_col].astype(str) == pilih_branch]
if pilih_client != "Semua": df_f = df_f[df_f[client_col].astype(str) == pilih_client]
if pilih_group != "Semua": df_f = df_f[df_f[group_col].astype(str) == pilih_group]

# Filter Khusus VBA Utilisasi Armada
if transporter_col in df_f.columns:
    df_f = df_f[df_f[transporter_col] == "GoTrans Logistics International"]

if status_col in df_f.columns:
    excluded_statuses = ["Cancel Order Approved", "Not Accepted", "Cancel Order Requested"]
    df_f = df_f[~df_f[status_col].isin(excluded_statuses)]


# --- ENGINE LOGIKA HARI KERJA (SLA) ---
id_holidays = holidays.ID(years=range(start_date.year, end_date.year + 1))
cuti_lebaran = set()
for d_obj, name in id_holidays.items():
    if "Idul Fitri" in name or "Lebaran" in name:
        for i in range(-2, 3): cuti_lebaran.add(d_obj + datetime.timedelta(days=i))

hari_kerja = 0
for d in pd.date_range(start_date, end_date):
    d_date = d.date()
    if d.weekday() == 6: continue # Minggu libur
    if d_date in cuti_lebaran: continue # Cuti lebaran libur
    if d_date in id_holidays: continue # Tanggal merah libur
    hari_kerja += 1

# --- PIVOT TABLE & AGREGASI ---
st.markdown(f"### 🚛 Hasil Utilisasi (SLA: {hari_kerja} Hari Kerja)")

try:
    # Memastikan format angka bisa dikalkulasi
    df_f[mrc_col] = pd.to_numeric(df_f[mrc_col], errors='coerce').fillna(0)
    df_f[rev_col] = pd.to_numeric(df_f[rev_col], errors='coerce').fillna(0)
    df_f['Work Day'] = hari_kerja
    
    # Kumpulan Metrik Cepat
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ritase (Order)", f"{len(df_f):,}")
    c2.metric("Armada Aktif", f"{df_f[nopol_col].nunique()} Unit")
    c3.metric("Total MRC", f"Rp {df_f[mrc_col].sum()/1e6:.1f} Jt")
    c4.metric("Total Revenue", f"Rp {df_f[rev_col].sum()/1e6:.1f} Jt")
    
    # Proses GroupBy (Mirip PivotTable VBA Tabular Form)
    pivot_df = df_f.groupby([nopol_col, def_col]).agg(
        Work_Day=('Work Day', 'mean'),
        Ritase=(order_col, 'count'),
        Total_MRC=(mrc_col, 'sum'),
        Total_Revenue=(rev_col, 'sum')
    ).reset_index()
    
    # Formatting mata uang untuk tampilan web
    pivot_df['Total_MRC'] = pivot_df['Total_MRC'].apply(lambda x: f"Rp {x:,.0f}")
    pivot_df['Total_Revenue'] = pivot_df['Total_Revenue'].apply(lambda x: f"Rp {x:,.0f}")
    pivot_df.rename(columns={'Work_Day': 'Work Day'}, inplace=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.dataframe(pivot_df, use_container_width=True, hide_index=True)
    
    # --- TOMBOL EKSTRAK EXCEL ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pivot_df.to_excel(writer, index=False, sheet_name='PivotUtilisasi')
    
    st.download_button(
        label="📥 Ekstrak Report Utilisasi ke Excel",
        data=buffer.getvalue(),
        file_name=f"Utilisasi_Armada_{bulan}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except KeyError as e:
    st.error(f"⚠️ Kolom yang dibutuhkan VBA lu tidak ditemukan di database: {e}")
