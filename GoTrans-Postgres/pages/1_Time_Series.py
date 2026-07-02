import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import datetime

st.set_page_config(page_title="Daily Performance", layout="wide")

# CSS Futuristis
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Daily Run-Rate & Performance")
engine = create_engine(st.secrets["SUPABASE_URL"].strip())

# Ambil bulan berjalan
today = datetime.date.today()
tabel_aktif = f"{today.year}-{today.month:02d}"

try:
    df = pd.read_sql(f'SELECT * FROM "{tabel_aktif}"', engine)
    
    # Deteksi kolom tanggal dan revenue
    date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date'])), df.columns[0])
    rev_col = df.columns[97]
    cost_col = df.columns[98]
    
    df[date_col] = pd.to_datetime(df[date_col])
    df['Revenue'] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
    df['Cost'] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)
    df['Margin'] = df['Revenue'] - df['Cost']
    
    # Grouping Harian
    df_daily = df.groupby(df[date_col].dt.date).agg({'Revenue':'sum', 'Cost':'sum', 'Margin':'sum'}).reset_index()
    df_daily.columns = ['Tanggal', 'Revenue', 'Cost', 'Margin']
    
    # Metrik Daily Run-Rate
    st.subheader(f"Performa Harian - {today.strftime('%B %Y')}")
    
    # Visualisasi
    fig = px.line(df_daily, x='Tanggal', y=['Revenue', 'Cost', 'Margin'], 
                  template="plotly_dark", 
                  title="Tren Daily Performance (Revenue, Cost, Margin)")
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabel Daily
    st.dataframe(df_daily.sort_values('Tanggal', ascending=False), use_container_width=True)
    
except Exception as e:
    st.error(f"Error load data harian: {e}")
