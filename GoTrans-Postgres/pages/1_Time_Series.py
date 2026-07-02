import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import datetime

st.set_page_config(page_title="Time Series Analysis", layout="wide")

# CSS Futuristis
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e293b 100%) !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Operational Performance & Time Series")
st.markdown("---")

engine = create_engine(st.secrets["SUPABASE_URL"].strip())

# --- FUNGSI LOAD DATA HARIAN ---
def get_daily_data(tabel_nama):
    try:
        df = pd.read_sql(f'SELECT * FROM "{tabel_nama}"', engine)
        date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date'])), df.columns[0])
        rev_col = df.columns[97]
        df[date_col] = pd.to_datetime(df[date_col])
        df['Revenue'] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
        # Group harian
        daily = df.groupby(df[date_col].dt.date)['Revenue'].sum().reset_index()
        daily.columns = ['Tanggal', 'Revenue']
        return daily
    except:
        return pd.DataFrame()

# --- LOGIKA TAHUNAN (12 BULAN TERAKHIR) ---
today = datetime.date.today()
tabel_ini = f"{today.year}-{today.month:02d}"
first_day_of_month = today.replace(day=1)
last_month = first_day_of_month - datetime.timedelta(days=1)
tabel_lalu = f"{last_month.year}-{last_month.month:02d}"

# Load data harian buat perbandingan bulan ini vs lalu
df_ini = get_daily_data(tabel_ini)
df_ini['Cumulative'] = df_ini['Revenue'].cumsum()
df_ini['Day'] = pd.to_datetime(df_ini['Tanggal']).dt.day

df_lalu = get_daily_data(tabel_lalu)
df_lalu['Cumulative'] = df_lalu['Revenue'].cumsum()
df_lalu['Day'] = pd.to_datetime(df_lalu['Tanggal']).dt.day

df_compare = pd.merge(df_ini, df_lalu, on='Day', suffixes=('_Ini', '_Lalu'), how='outer').fillna(0)

# --- LOAD DATA TAHUNAN (DAY BY DAY) ---
@st.cache_data
def get_annual_data():
    all_data = []
    for i in range(12):
        d = today - pd.DateOffset(months=i)
        tabel = f"{d.year}-{d.month:02d}"
        all_data.append(get_daily_data(tabel))
    return pd.concat(all_data, ignore_index=True)

df_annual = get_annual_data()

# --- TAMPILAN DASHBOARD ---
tab1, tab2 = st.tabs(["🚀 Daily Run-Rate (MoM)", "📅 Annual Trend (Day-to-Day)"])

with tab1:
    st.markdown("### Tren Cumulative Revenue (Juli vs Juni)")
    col1, col2, col3 = st.columns(3)
    current_day = today.day
    row = df_compare[df_compare['Day'] == current_day]
    if not row.empty:
        r = row.iloc[0]
        col1.metric(f"Rev Tgl {current_day} (Ini)", f"Rp {r['Revenue_Ini']/1e6:,.1f} Jt")
        col2.metric(f"Rev Tgl {current_day} (Lalu)", f"Rp {r['Revenue_Lalu']/1e6:,.1f} Jt")
        growth = ((r['Revenue_Ini'] - r['Revenue_Lalu']) / r['Revenue_Lalu'] * 100) if r['Revenue_Lalu'] > 0 else 100
        col3.metric("Growth Harian", f"{growth:.1f}%", delta=f"{growth:.1f}%")

    df_plot = df_compare.melt(id_vars=['Day'], value_vars=['Cumulative_Ini', 'Cumulative_Lalu'], var_name='Periode', value_name='Total_Revenue')
    fig = px.line(df_plot, x='Day', y='Total_Revenue', color='Periode', template="plotly_dark", markers=True, color_discrete_map={'Cumulative_Ini': '#38bdf8', 'Cumulative_Lalu': '#94a3b8'})
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Analisis Harian 12 Bulan Terakhir")
    # Line chart lebih masuk akal daripada bar chart untuk 365 data points
    fig_yr = px.line(df_annual.sort_values('Tanggal'), x='Tanggal', y='Revenue', template="plotly_dark", color_discrete_sequence=['#10b981'])
    fig_yr.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig_yr, use_container_width=True)
    
    st.dataframe(df_annual.sort_values('Tanggal', ascending=False), use_container_width=True)
