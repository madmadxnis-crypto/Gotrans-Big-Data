import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import datetime

# ... (CSS Futuristis sama seperti sebelumnya) ...

# --- FUNGSI LOAD DATA HARIAN ---
def get_daily_data(tabel_nama):
    try:
        df = pd.read_sql(f'SELECT * FROM "{tabel_nama}"', engine)
        date_col = next((c for c in df.columns if any(k in c.lower() for k in ['tanggal', 'tgl', 'date'])), df.columns[0])
        rev_col = df.columns[97]
        df[date_col] = pd.to_datetime(df[date_col])
        df['Revenue'] = pd.to_numeric(df[rev_col], errors='coerce').fillna(0)
        # Group per tanggal
        daily = df.groupby(df[date_col].dt.date)['Revenue'].sum().reset_index()
        daily.columns = ['Tanggal', 'Revenue']
        return daily
    except:
        return pd.DataFrame()

# --- LOGIKA KUMULATIF TAHUNAN ---
# Ambil data 12 bulan terakhir
today = datetime.date.today()
all_data = []
for i in range(12):
    d = today - pd.DateOffset(months=i)
    tabel = f"{d.year}-{d.month:02d}"
    all_data.append(get_daily_data(tabel))

df_annual = pd.concat(all_data, ignore_index=True)
df_annual = df_annual.sort_values('Tanggal')

# INI KUNCINYA: Kumulatifkan Revenue dari awal data sampai hari ini
df_annual['Cumulative'] = df_annual['Revenue'].cumsum()

# --- TAMPILAN DASHBOARD ---
# ... (Simpan bagian Daily Run-Rate MoM lu) ...

with tab2:
    st.markdown("### 📈 Cumulative Revenue (Annual Trend)")
    
    # Line chart buat nampilin cumulative
    fig_yr = px.line(df_annual, x='Tanggal', y='Cumulative', 
                     template="plotly_dark", 
                     color_discrete_sequence=['#10b981'])
    
    fig_yr.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        xaxis_rangeslider_visible=True,
        yaxis_title="Total Akumulasi Revenue (Rp)"
    )
    st.plotly_chart(fig_yr, use_container_width=True)
    
    # Tabel Data (Balikin ke urutan terbaru di atas)
    st.dataframe(df_annual.sort_values('Tanggal', ascending=False), use_container_width=True)
