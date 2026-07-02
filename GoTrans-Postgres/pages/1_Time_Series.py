import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.graph_objects as go
import datetime

st.set_page_config(page_title="Time Series Analysis", layout="wide")

engine = create_engine(st.secrets["SUPABASE_URL"].strip())

def get_df_by_month(year, month):
    tabel = f"{year}-{int(month):02d}"
    try:
        df = pd.read_sql(f'SELECT * FROM "{tabel}"', engine)
        date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date'])), df.columns[0])
        rev_col = df.columns[97]
        df[date_col] = pd.to_datetime(df[date_col])
        df['Revenue'] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
        # Group harian & buat kolom 'Day' biar bisa disejajarin (tgl 1 vs tgl 1, dst)
        df_daily = df.groupby(df[date_col].dt.day)['Revenue'].sum().reset_index()
        df_daily.columns = ['Day', 'Revenue']
        df_daily['Cumulative'] = df_daily['Revenue'].cumsum()
        return df_daily
    except:
        return pd.DataFrame(columns=['Day', 'Revenue', 'Cumulative'])

# Ambil data bulan ini dan bulan lalu
today = datetime.date.today()
df_ini = get_df_by_month(today.year, today.month)
# Logic bulan lalu
last_month = today.replace(day=1) - datetime.timedelta(days=1)
df_lalu = get_df_by_month(last_month.year, last_month.month)

st.title(f"🚀 Cumulative Revenue: {today.strftime('%B')} vs {last_month.strftime('%B')}")

# Plotting Comparison
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_ini['Day'], y=df_ini['Cumulative'], name=f'Juli 2026 (Cumulative)', line=dict(color='#38bdf8', width=4)))
fig.add_trace(go.Scatter(x=df_lalu['Day'], y=df_lalu['Cumulative'], name=f'Juni 2026 (Cumulative)', line=dict(color='#94a3b8', width=4, dash='dash')))

fig.update_layout(
    template="plotly_dark",
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    xaxis_title="Tanggal", yaxis_title="Total Revenue (Rp)",
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# Tabel Perbandingan Ringkas
st.subheader("Detail Perbandingan")
comparison = pd.merge(df_ini[['Day', 'Revenue']], df_lalu[['Day', 'Revenue']], on='Day', suffixes=('_Ini', '_Lalu'))
comparison['Diff'] = comparison['Revenue_Ini'] - comparison['Revenue_Lalu']
st.dataframe(comparison.sort_values('Day', ascending=False), use_container_width=True)
