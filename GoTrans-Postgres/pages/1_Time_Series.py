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

st.title("📊 Daily Run-Rate & Cumulative Performance")
st.markdown("---")

engine = create_engine(st.secrets["SUPABASE_URL"].strip())

def process_daily_data(tabel_nama):
    try:
        df = pd.read_sql(f'SELECT * FROM "{tabel_nama}"', engine)
        date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date'])), df.columns[0])
        rev_col = df.columns[97] # Sesuai index 97 lu
        
        df[date_col] = pd.to_datetime(df[date_col])
        df['Revenue'] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
        
        # Group per hari (1-31)
        daily = df.groupby(df[date_col].dt.day)['Revenue'].sum().reset_index()
        daily.columns = ['Day', 'Revenue']
        # Hitung Kumulatif
        daily['Cumulative'] = daily['Revenue'].cumsum()
        return daily
    except:
        return pd.DataFrame(columns=['Day', 'Revenue', 'Cumulative'])

# Logic ambil bulan ini dan bulan lalu
today = datetime.date.today()
tabel_ini = f"{today.year}-{today.month:02d}"

# Hitung bulan lalu
first_day_of_month = today.replace(day=1)
last_month = first_day_of_month - datetime.timedelta(days=1)
tabel_lalu = f"{last_month.year}-{last_month.month:02d}"

# Load data
df_ini = process_daily_data(tabel_ini)
df_lalu = process_daily_data(tabel_lalu)

# Gabungin data biar bisa dibandingin (1 vs 1, 2 vs 2, dst)
df_compare = pd.merge(df_ini, df_lalu, on='Day', suffixes=('_Ini', '_Lalu'))

# Tampilan Metrik untuk tanggal hari ini
current_day = today.day
if current_day in df_compare['Day'].values:
    row = df_compare[df_compare['Day'] == current_day].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Revenue Tgl {current_day} (Ini)", f"Rp {row['Revenue_Ini']/1e6:,.1f} Jt")
    col2.metric(f"Revenue Tgl {current_day} (Lalu)", f"Rp {row['Revenue_Lalu']/1e6:,.1f} Jt")
    
    diff = row['Revenue_Ini'] - row['Revenue_Lalu']
    growth = (diff / row['Revenue_Lalu'] * 100) if row['Revenue_Lalu'] > 0 else 100
    col3.metric("Growth Harian", f"{growth:.1f}%", delta=f"{growth:.1f}%")

# Visualisasi Cumulative
st.markdown("### Tren Cumulative Revenue (Day-to-Day)")
# Reformating buat plotly biar bisa line chart
df_plot = df_compare.melt(id_vars=['Day'], value_vars=['Cumulative_Ini', 'Cumulative_Lalu'], var_name='Periode', value_name='Total_Revenue')

fig = px.line(df_plot, x='Day', y='Total_Revenue', color='Periode', 
              template="plotly_dark", markers=True,
              color_discrete_map={'Cumulative_Ini': '#38bdf8', 'Cumulative_Lalu': '#94a3b8'})
fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Detail Perbandingan Harian")
st.dataframe(df_compare.sort_values('Day', ascending=False), use_container_width=True)
