import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
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

# --- FUNGSI UTAMA ---
def process_daily_data(tabel_nama):
    try:
        df = pd.read_sql(f'SELECT * FROM "{tabel_nama}"', engine)
        date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date'])), df.columns[0])
        rev_col = df.columns[97]
        df[date_col] = pd.to_datetime(df[date_col])
        df['Revenue'] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
        daily = df.groupby(df[date_col].dt.day)['Revenue'].sum().reset_index()
        daily.columns = ['Day', 'Revenue']
        daily['Cumulative'] = daily['Revenue'].cumsum()
        return daily
    except:
        return pd.DataFrame(columns=['Day', 'Revenue', 'Cumulative'])

# --- DATA HARIAN (BULAN INI VS LALU) ---
today = datetime.date.today()
tabel_ini = f"{today.year}-{today.month:02d}"
first_day_of_month = today.replace(day=1)
last_month = first_day_of_month - datetime.timedelta(days=1)
tabel_lalu = f"{last_month.year}-{last_month.month:02d}"

df_ini = process_daily_data(tabel_ini)
df_lalu = process_daily_data(tabel_lalu)
df_compare = pd.merge(df_ini, df_lalu, on='Day', suffixes=('_Ini', '_Lalu'), how='outer').fillna(0)

# --- ANALISIS TAHUNAN (LAST 12 MONTHS) ---
st.markdown("### 🗓️ Annual Performance (Last 12 Months)")
data_tahunan = []
for i in range(12):
    d = today - pd.DateOffset(months=i)
    tabel_tahunan = f"{d.year}-{d.month:02d}"
    try:
        df_yr = pd.read_sql(f'SELECT * FROM "{tabel_tahunan}"', engine)
        rev = pd.to_numeric(df_yr[df_yr.columns[97]], errors='coerce').sum()
        data_tahunan.append({'Bulan': tabel_tahunan, 'Revenue': rev})
    except:
        continue

df_tahunan = pd.DataFrame(data_tahunan).sort_values('Bulan')

# --- TAMPILAN DASHBOARD ---
tab1, tab2 = st.tabs(["🚀 Daily Cumulative", "📊 Annual Trend"])

with tab1:
    col1, col2, col3 = st.columns(3)
    current_day = today.day
    row = df_compare[df_compare['Day'] == current_day]
    if not row.empty:
        r = row.iloc[0]
        col1.metric(f"Rev Tgl {current_day} (Ini)", f"Rp {r['Revenue_Ini']/1e6:,.1f} Jt")
        col2.metric(f"Rev Tgl {current_day} (Lalu)", f"Rp {r['Revenue_Lalu']/1e6:,.1f} Jt")
        growth = ((r['Revenue_Ini'] - r['Revenue_Lalu']) / r['Revenue_Lalu'] * 100) if r['Revenue_Lalu'] > 0 else 100
        col3.metric("Growth Harian", f"{growth:.1f}%", delta=f"{growth:.1f}%")

    st.markdown("### Tren Cumulative Revenue (Juli vs Juni)")
    df_plot = df_compare.melt(id_vars=['Day'], value_vars=['Cumulative_Ini', 'Cumulative_Lalu'], var_name='Periode', value_name='Total_Revenue')
    fig = px.line(df_plot, x='Day', y='Total_Revenue', color='Periode', template="plotly_dark", markers=True, color_discrete_map={'Cumulative_Ini': '#38bdf8', 'Cumulative_Lalu': '#94a3b8'})
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Revenue 12 Bulan Terakhir")
    fig_yr = px.bar(df_tahunan, x='Bulan', y='Revenue', text_auto='.2s', template="plotly_dark", color_discrete_sequence=['#10b981'])
    fig_yr.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_yr, use_container_width=True)
    st.dataframe(df_tahunan.sort_values('Bulan', ascending=False), use_container_width=True)
