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

st.set_page_config(page_title="Utilisasi Driver Pintar", page_icon="👨‍✈️", layout="wide")

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

# --- NAVIGASI BACK TO HOME SEJAJAR JUDUL ---
col_title, col_home = st.columns([4, 1])
with col_title:
    st.markdown("<h2 style='margin-top: 0px; color: #ffffff; font-weight: 800;'>📝Utilisasi Driver📝</h2>", unsafe_allow_html=True)
with col_home:
    if st.button("🏠 Kembali ke Home", use_container_width=True):
        st.switch_page("app.py")

st.markdown("<p style='color: #94a3b8; margin-top: -10px;'>Otomatis mendeteksi Hari Kerja</p>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# --- KONEKSI & PARSING NAMA TABEL ---
engine = create_engine(st.secrets["SUPABASE_URL"].strip())
try:
    semua_tabel = inspect(engine).get_table_names()
    tabel_valid = [t for t in semua_tabel if '-' in t]
except Exception:
    tabel_valid = []

if not tabel_valid:
    st.warning("Database belum tersedia atau format nama tabel tidak dikenali.")
    st.stop()

bulan_set, tahun_set = set(), set()
for t in tabel_valid:
    parts = t.split('-')
    if len(parts) >= 2:
        if len(parts[0]) == 4:
            tahun_set.add(parts[0])
            bulan_set.add(parts[1])
        else:
            bulan_set.add(parts[0])
            tahun_set.add(parts[1])

# --- BARIS 1: FILTER WAKTU (PRESET & MANUAL) ---
col_preset, col_bln, col_thn, col_start, col_end = st.columns([1.5, 1, 1, 1.2, 1.2])

with col_preset:
    preset = st.selectbox("Filter Waktu:", ["Bulan", "All Time", "Last 3 Months", "Last 6 Months", "Last 1 Year"])

with col_bln:
    pilih_bulan = st.selectbox("Bulan:", sorted(list(bulan_set)), disabled=(preset != "Bulan Spesifik"))
with col_thn:
    pilih_tahun = st.selectbox("Tahun:", sorted(list(tahun_set), reverse=True), disabled=(preset != "Bulan Spesifik"))

df_list = []
if preset == "Bulan Spesifik":
    target_table = f"{pilih_tahun}-{pilih_bulan}" if f"{pilih_tahun}-{pilih_bulan}" in tabel_valid else f"{pilih_bulan}-{pilih_tahun}"
    if target_table in tabel_valid:
        df_list.append(pd.read_sql(f'SELECT * FROM "{target_table}"', engine))
    else:
        st.error(f"⚠️ Data untuk {pilih_bulan}-{pilih_tahun} tidak ditemukan.")
        st.stop()
else:
    with st.spinner(f"Menyatukan data {preset} dari seluruh tabel di database..."):
        for t in tabel_valid:
            try:
                df_list.append(pd.read_sql(f'SELECT * FROM "{t}"', engine))
            except:
                pass

if not df_list:
    st.error("Gagal menarik data dari database.")
    st.stop()

df = pd.concat(df_list, ignore_index=True)

# Deteksi Kolom, AL = index 37
date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date', 'surat_jalan'])), df.columns[0])
branch_col = df.columns[3] if len(df.columns) > 3 else df.columns[0]
client_col = df.columns[12] if len(df.columns) > 12 else df.columns[0]
group_col = df.columns[7] if len(df.columns) > 7 else df.columns[0]

# --- PERUBAHAN UTAMA: Deteksi Kolom Driver ---
driver_col = df.columns[37] if len(df.columns) > 37 else next((c for c in df.columns if 'driver' in c.lower()), "Driver")
def_col = next((c for c in df.columns if 'definition' in c.lower()), "Definition")
transporter_col = next((c for c in df.columns if 'transporter' in c.lower()), "Nama Transporter")
status_col = next((c for c in df.columns if 'status pengiriman' in c.lower()), "Status Pengiriman")
order_col = next((c for c in df.columns if 'no order' in c.lower() or 'order' in c.lower()), "No Order")
mrc_col = next((c for c in df.columns if 'mrc' in c.lower()), "Total MRC")
rev_col = df.columns[97] if len(df.columns) > 97 else "Revenue"

df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df_valid = df.dropna(subset=[date_col])

today = datetime.date.today()
start_of_month = today.replace(day=1) 

min_db_date = df_valid[date_col].min().date() if not df_valid.empty else start_of_month
max_db_date = df_valid[date_col].max().date() if not df_valid.empty else today

if preset == "All Time":
    def_start, def_end = min_db_date, max_db_date
elif preset == "Last 3 Months":
    def_start, def_end = (pd.to_datetime(today) - pd.DateOffset(months=3)).date(), today
elif preset == "Last 6 Months":
    def_start, def_end = (pd.to_datetime(today) - pd.DateOffset(months=6)).date(), today
elif preset == "Last 1 Year":
    def_start, def_end = (pd.to_datetime(today) - pd.DateOffset(years=1)).date(), today
else: 
    def_start, def_end = start_of_month, today

if def_start > def_end: 
    def_start = def_end

with col_start: start_date = st.date_input("Mulai Tanggal:", value=def_start, format="DD/MM/YYYY")
with col_end: end_date = st.date_input("Sampai Tanggal:", value=def_end, format="DD/MM/YYYY")

if start_date > end_date:
    st.error("⚠️ Mulai Tanggal tidak boleh lebih besar dari Sampai Tanggal.")
    st.stop()

df_temp = df_valid[(df_valid[date_col].dt.date >= start_date) & (df_valid[date_col].dt.date <= end_date)].copy()

# --- BARIS 2: FILTER SALING MENGUNCI LOKASI & VENDOR ---
col_t, col_b, col_c, col_g = st.columns(4)

with col_t:
    opsi_t = ["Semua"] + sorted(df_temp[transporter_col].astype(str).dropna().unique().tolist())
    default_idx_t = opsi_t.index("GoTrans Logistics International") if "GoTrans Logistics International" in opsi_t else 0
    pilih_transporter = st.selectbox("Transporter:", opsi_t, index=default_idx_t)
    if pilih_transporter != "Semua": 
        df_temp = df_temp[df_temp[transporter_col].astype(str) == pilih_transporter]

with col_b:
    opsi_b = ["Semua"] + sorted(df_temp[branch_col].astype(str).dropna().unique().tolist())
    pilih_branch = st.selectbox("Branch:", opsi_b)
    if pilih_branch != "Semua": df_temp = df_temp[df_temp[branch_col].astype(str) == pilih_branch]

with col_c:
    opsi_c = ["Semua"] + sorted(df_temp[client_col].astype(str).dropna().unique().tolist())
    pilih_client = st.selectbox("Client:", opsi_c)
    if pilih_client != "Semua": df_temp = df_temp[df_temp[client_col].astype(str) == pilih_client]

with col_g:
    opsi_g = ["Semua"] + sorted(df_temp[group_col].astype(str).dropna().unique().tolist())
    pilih_group = st.selectbox("Group:", opsi_g)
    if pilih_group != "Semua": df_temp = df_temp[df_temp[group_col].astype(str) == pilih_group]


# --- BARIS 3: FILTER DRIVER & TYPE MOBIL (MULTI-SELECT) ---
col_def, col_driver = st.columns(2)

with col_def:
    opsi_def = sorted(df_temp[def_col].astype(str).dropna().unique().tolist())
    pilih_def = st.multiselect("Type Mobil:", opsi_def, placeholder="bisa pilih banyak tipe")
    if pilih_def:
        df_temp = df_temp[df_temp[def_col].astype(str).isin(pilih_def)]

with col_driver:
    opsi_driver = sorted(df_temp[driver_col].astype(str).dropna().unique().tolist())
    pilih_driver = st.multiselect("Nama Driver :", opsi_driver, placeholder="bisa pilih banyak Driver")
    if pilih_driver:
        df_temp = df_temp[df_temp[driver_col].astype(str).isin(pilih_driver)]


# Finalisasi Dataframe Terfilter
df_f = df_temp.copy()

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

def format_rp(angka):
    if angka >= 1e9: 
        return f"Rp {angka/1e9:,.2f} M"
    elif angka >= 1e6: 
        return f"Rp {angka/1e6:,.1f} Jt"
    return f"Rp {angka:,.0f}"

# --- PIVOT TABLE & AGREGASI ---
st.markdown(f"### 👨‍✈️ Utilisasi (SLA: {hari_kerja} Hari Kerja)")

try:
    df_f[mrc_col] = pd.to_numeric(df_f[mrc_col], errors='coerce').fillna(0)
    df_f[rev_col] = pd.to_numeric(df_f[rev_col], errors='coerce').fillna(0)
    df_f['Work Day'] = hari_kerja
    
    total_mrc_rp = df_f[mrc_col].sum()
    total_rev_rp = df_f[rev_col].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ritase (Sales Order)", f"{len(df_f):,}")
    c2.metric("Driver Aktif", f"{df_f[driver_col].nunique()} Orang")
    c3.metric("Total MRC", format_rp(total_mrc_rp))
    c4.metric("Total Revenue", format_rp(total_rev_rp))
    
    # Pivot bedasarkan Driver dan Definition (Type Mobil)
    pivot_df = df_f.groupby([driver_col, def_col]).agg(
        Work_Day=('Work Day', 'mean'),
        Ritase=(order_col, 'count'),
        Total_MRC=(mrc_col, 'sum'),
        Total_Revenue=(rev_col, 'sum')
    ).reset_index()
    
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
        filter_info = pd.DataFrame({
            'PARAMETER': [
                'Mode Waktu', 'Bulan/Tahun DB', 'Rentang Tanggal', 'SLA (Hari Kerja)', 
                'Filter Transporter', 'Filter Branch', 'Filter Client', 'Filter Group',
                'Filter Definition', 'Filter Driver'
            ],
            'NILAI YANG DIGUNAKAN': [
                preset,
                f"{pilih_bulan}-{pilih_tahun}" if preset == "Bulan Spesifik" else "Semua Tabel",
                f"{start_date.strftime('%d %b %Y')} s/d {end_date.strftime('%d %b %Y')}", 
                f"{hari_kerja} Hari", 
                pilih_transporter,
                pilih_branch, 
                pilih_client, 
                pilih_group,
                ", ".join(pilih_def) if pilih_def else "Semua",
                ", ".join(pilih_driver) if pilih_driver else "Semua"
            ]
        })
        
        filter_info.to_excel(writer, index=False, sheet_name='PivotUtilisasi', startrow=0, startcol=0)
        start_row_pivot = len(filter_info) + 2
        pivot_excel.to_excel(writer, index=False, sheet_name='PivotUtilisasi', startrow=start_row_pivot, startcol=0)
    
    st.download_button(
        label="📥 Ekstrak Report & Filter ke Excel",
        data=buffer.getvalue(),
        file_name=f"Utilisasi_Driver_{preset.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except KeyError as e:
    st.error(f"⚠️ Kolom tidak ditemukan di database: {e}")
