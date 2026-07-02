import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import datetime
import calendar

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
        return pd.DataFrame(columns=['Tanggal', 'Revenue'])

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

# --- LOAD DATA TAHUNAN (DAY BY DAY, per-bulan biar bisa di-overlay by tanggal) ---
BULAN_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

@st.cache_data
def get_annual_data():
    all_data = []
    for i in range(11, -1, -1):  # urut dari 11 bulan lalu -> bulan ini
        d = today - pd.DateOffset(months=i)
        tabel = f"{d.year}-{d.month:02d}"
        df_bulan = get_daily_data(tabel)
        if df_bulan.empty:
            continue
        df_bulan = df_bulan.sort_values('Tanggal').reset_index(drop=True)
        df_bulan['Day'] = pd.to_datetime(df_bulan['Tanggal']).dt.day
        df_bulan['Cumulative'] = df_bulan['Revenue'].cumsum()
        df_bulan['Bulan'] = f"{BULAN_ID[d.month]} {d.year}"
        df_bulan['BulanUrut'] = d.year * 100 + d.month  # buat sorting legend biar kronologis
        all_data.append(df_bulan)
    if not all_data:
        return pd.DataFrame(columns=['Tanggal', 'Revenue', 'Day', 'Cumulative', 'Bulan', 'BulanUrut'])
    return pd.concat(all_data, ignore_index=True)

df_annual = get_annual_data()

# =========================================================
# --- PERHITUNGAN MoM GROWTH & DAILY AVERAGE RUN-RATE ---
# =========================================================
current_day = today.day
days_in_month_ini = calendar.monthrange(today.year, today.month)[1]

# --- MoM: total revenue bulan ini (MTD) vs periode yang sama bulan lalu ---
total_mtd_ini = df_ini['Revenue'].sum()
total_mtd_lalu = df_lalu[df_lalu['Day'] <= current_day]['Revenue'].sum()

mom_growth_pct = (
    ((total_mtd_ini - total_mtd_lalu) / total_mtd_lalu * 100)
    if total_mtd_lalu > 0 else 0
)
mom_growth_abs = total_mtd_ini - total_mtd_lalu

# --- Daily Average Run-Rate ---
# rata-rata revenue per hari yang sudah berjalan, lalu diproyeksikan ke total hari dalam bulan
daily_avg = total_mtd_ini / current_day if current_day > 0 else 0
projected_total_bulan_ini = daily_avg * days_in_month_ini

total_bulan_lalu_penuh = df_lalu['Revenue'].sum()
proyeksi_vs_bulan_lalu_pct = (
    ((projected_total_bulan_ini - total_bulan_lalu_penuh) / total_bulan_lalu_penuh * 100)
    if total_bulan_lalu_penuh > 0 else 0
)

# --- TAMPILAN DASHBOARD ---
tab1, tab2 = st.tabs(["🚀 Daily Run-Rate (MoM)", "📅 Annual Trend (Day-to-Day)"])

with tab1:
    st.markdown("### 🔥 Key Metrics: MoM Growth & Run-Rate")

    m1, m2, m3, m4 = st.columns(4)

    # 1) Revenue MTD bulan ini vs bulan lalu (periode sama) -> delta = growth %
    m1.metric(
        label=f"Revenue MTD ({tabel_ini})",
        value=f"Rp {total_mtd_ini/1e6:,.1f} Jt",
        delta=f"{mom_growth_pct:.1f}% vs bulan lalu"
    )

    # 2) Revenue periode sama bulan lalu, sebagai pembanding
    m2.metric(
        label=f"Revenue MTD ({tabel_lalu}, s/d hari ke-{current_day})",
        value=f"Rp {total_mtd_lalu/1e6:,.1f} Jt",
        delta=f"Rp {mom_growth_abs/1e6:,.1f} Jt selisih"
    )

    # 3) Daily Average Run-Rate
    m3.metric(
        label="Rata-rata Revenue / Hari (Bulan Ini)",
        value=f"Rp {daily_avg/1e6:,.1f} Jt",
        delta=f"{current_day} hari berjalan"
    )

    # 4) Proyeksi total akhir bulan vs total bulan lalu (full month)
    m4.metric(
        label=f"Proyeksi Total Akhir Bulan ({tabel_ini})",
        value=f"Rp {projected_total_bulan_ini/1e6:,.1f} Jt",
        delta=f"{proyeksi_vs_bulan_lalu_pct:.1f}% vs total bulan lalu"
    )

    st.markdown("---")
    st.markdown("### Tren Cumulative Revenue (Bulan Ini vs Bulan Lalu)")

    df_plot = df_compare.melt(id_vars=['Day'], value_vars=['Cumulative_Ini', 'Cumulative_Lalu'], var_name='Periode', value_name='Total_Revenue')
    fig = px.line(df_plot, x='Day', y='Total_Revenue', color='Periode', template="plotly_dark", markers=True, color_discrete_map={'Cumulative_Ini': '#38bdf8', 'Cumulative_Lalu': '#94a3b8'})

    # Garis proyeksi run-rate (linear dari data yang ada sampai akhir bulan)
    fig.add_scatter(
        x=[current_day, days_in_month_ini],
        y=[total_mtd_ini, projected_total_bulan_ini],
        mode='lines',
        name='Proyeksi Run-Rate',
        line=dict(color='#f59e0b', dash='dash')
    )

    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Perbandingan Cumulative Revenue per Tanggal (12 Bulan Terakhir)")
    st.caption("Sumbu X = tanggal (1-31), tiap garis = satu bulan, sehingga tgl 3 Januari vs tgl 3 Februari vs tgl 3 Maret dst. bisa langsung dibandingkan.")

    if df_annual.empty:
        st.warning("Data belum tersedia.")
    else:
        urutan_bulan = (
            df_annual[['Bulan', 'BulanUrut']]
            .drop_duplicates()
            .sort_values('BulanUrut')['Bulan']
            .tolist()
        )

        fig_yr = px.line(
            df_annual.sort_values(['BulanUrut', 'Day']),
            x='Day',
            y='Cumulative',
            color='Bulan',
            category_orders={'Bulan': urutan_bulan},
            template="plotly_dark",
            markers=True,
            labels={'Day': 'Tanggal', 'Cumulative': 'Cumulative Revenue', 'Bulan': 'Bulan'}
        )
        fig_yr.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(dtick=1, title="Tanggal"),
            legend_title_text='Bulan'
        )
        st.plotly_chart(fig_yr, use_container_width=True)

    st.markdown("---")
    st.markdown("### Data Detail Harian")
    st.dataframe(
        df_annual.sort_values(['BulanUrut', 'Day'], ascending=[False, False])[['Tanggal', 'Bulan', 'Day', 'Revenue', 'Cumulative']],
        use_container_width=True
    )
