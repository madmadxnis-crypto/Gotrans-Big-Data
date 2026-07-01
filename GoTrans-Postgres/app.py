import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.express as px
import datetime
import io

st.set_page_config(page_title="Gotrans TMS Dashboard", page_icon="🚚", layout="wide")

# CSS Futuristik
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important; color: #f8fafc !important; }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.7) !important; backdrop-filter: blur(10px) !important; padding: 20px !important; border-radius: 16px !important; border: 1px solid rgba(56, 189, 248, 0.2) !important; min-height: 160px !important; }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2rem !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# Header & Logo
c1, c2, c3 = st.columns([1.5, 2, 1.5])
with c2: st.image("GoTrans-Postgres/logo_gobel.jpg", use_container_width=True)
st.markdown("<h1 style='text-align: center;'>Gotrans Operational Dashboard</h1>", unsafe_allow_html=True)

# Koneksi
engine = create_engine(st.secrets["SUPABASE_URL"].strip())
bulan = st.sidebar.selectbox("Bulan Aktif", sorted([t for t in inspect(engine).get_table_names() if '-' in t], reverse=True))
df = pd.read_sql(f'SELECT * FROM "{bulan}"', engine)

# Deteksi Kolom & Tanggal
date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date', 'surat_jalan'])), df.columns[0])
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df = df.dropna(subset=[date_col])

# Filter Row
c_judul, c_filter = st.columns([2.5, 1.5])
with c_filter:
    dr = st.date_input("Rentang:", value=(df[date_col].min(), df[date_col].max()), format="DD/MM/YYYY", label_visibility="collapsed")
    start, end = (dr[0], dr[1]) if isinstance(dr, (list, tuple)) else (dr, dr)

df_f = df[(df[date_col].dt.date >= start) & (df[date_col].dt.date <= end)].copy()

# Filter Ops
c_b, c_c, c_g = st.columns(3)
b = c_b.selectbox("Branch:", ["Semua"] + sorted(df[df.columns[3]].dropna().unique().tolist()))
c = c_c.selectbox("Client:", ["Semua"] + sorted(df[df.columns[12]].dropna().unique().tolist()))
g = c_g.selectbox("Group:", ["Semua"] + sorted(df[df.columns[7]].dropna().unique().tolist()))

if b != "Semua": df_f = df_f[df_f[df.columns[3]] == b]
if c != "Semua": df_f = df_f[df_f[df.columns[12]] == c]
if g != "Semua": df_f = df_f[df_f[df.columns[7]] == g]

# Metrik Finansial
df_f['Rev'] = pd.to_numeric(df_f.iloc[:, 97], errors='coerce').fillna(0)
df_f['Cost'] = pd.to_numeric(df_f.iloc[:, 98], errors='coerce').fillna(0)
df_f.loc[df_f['Cost'] == 0, 'Cost'] = pd.to_numeric(df_f.iloc[:, 102], errors='coerce').fillna(0) + pd.to_numeric(df_f.iloc[:, 103], errors='coerce').fillna(0)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Revenue", f"Rp {df_f['Rev'].sum()/1e9:.2f} M")
m2.metric("Cost", f"Rp {df_f['Cost'].sum()/1e9:.2f} M")
m3.metric("Margin", f"{(df_f['Rev'].sum()-df_f['Cost'].sum())/1e9:.2f} M")
m4.metric("Orders", f"{len(df_f):,}")

# Ekstrak
buf = io.BytesIO()
with pd.ExcelWriter(buf) as w: df_f.to_excel(w, index=False)
st.download_button("📥 Ekstrak Excel", buf.getvalue(), f"Gotrans_{bulan}.xlsx")

# Grafik
df_d = df_f.groupby(df_f[date_col].dt.date).agg({'Rev':'sum', 'Cost':'sum'}).reset_index()
st.plotly_chart(px.line(df_d, x=date_col, y=['Rev', 'Cost'], template="plotly_dark"), use_container_width=True)
