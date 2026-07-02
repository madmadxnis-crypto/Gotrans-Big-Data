import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

st.set_page_config(page_title="Time Series Analysis", layout="wide")

# CSS Futuristis
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Time Series & MoM Growth")
st.markdown("---")

engine = create_engine(st.secrets["SUPABASE_URL"].strip())

def get_monthly_total(tabel_nama):
    try:
        df = pd.read_sql(f'SELECT * FROM "{tabel_nama}"', engine)
        rev_col = df.columns[97]
        # Total Revenue
        return pd.to_numeric(df[rev_col], errors='coerce').sum()
    except:
        return 0

# 1. Ambil list tabel untuk dibandingin
tabel_valid = sorted([t for t in pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public'", engine)['table_name'] if '-' in t])

# 2. Logic Perbandingan MoM
if len(tabel_valid) >= 2:
    data_tren = []
    for t in tabel_valid:
        total = get_monthly_total(t)
        data_tren.append({'Bulan': t, 'Revenue': total})
    
    df_tren = pd.DataFrame(data_tren)
    
    # Hitung Growth %
    df_tren['Growth (%)'] = df_tren['Revenue'].pct_change() * 100
    
    # Tampilan Metrik Perbandingan Bulan Terakhir
    bln_ini = df_tren.iloc[-1]
    bln_lalu = df_tren.iloc[-2]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue Bulan Ini", f"Rp {bln_ini['Revenue']/1e6:,.1f} Jt")
    col2.metric("Revenue Bulan Lalu", f"Rp {bln_lalu['Revenue']/1e6:,.1f} Jt")
    col3.metric("Growth", f"{bln_ini['Growth (%)']:.1f}%", delta=f"{bln_ini['Growth (%)']:.1f}%")

    # Visualisasi
    st.markdown("### Tren Pertumbuhan Revenue")
    fig = px.bar(df_tren, x='Bulan', y='Revenue', text_auto='.2s', template="plotly_dark", color_discrete_sequence=['#38bdf8'])
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Detail Pertumbuhan per Bulan")
    st.dataframe(df_tren, use_container_width=True)

else:
    st.warning("Butuh minimal 2 tabel bulan yang berbeda untuk analisis tren!")
