import streamlit as st
import pandas as pd
import glob
import plotly.express as px
import plotly.graph_objects as go
import io
import datetime

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="GoTrans Executive Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# CSS (CLEAN UI & MULTISELECT FIX)
# =====================================================
st.markdown("""
<style>
    .stApp { background-color: #F4F7F6; }
    
    label[data-testid="stWidgetLabel"] p {
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    
    .fin-card {
        background: #FFFFFF;
        padding: 20px 10px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        border-bottom: 4px solid #F97316; 
        text-align: center;
        transition: transform 0.2s ease-in-out;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 135px; 
    }
    .fin-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }
    .fin-title {
        color: #64748B;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    .fin-value {
        color: #0F172A;
        font-size: 26px; 
        font-weight: 800;
        word-break: break-word;
    }
    
    .mini-donut-container {
        position: relative;
        width: 50px;
        height: 50px;
        margin: 5px auto;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .mini-donut-hole {
        width: 30px;
        height: 30px;
        background: #FFFFFF;
        border-radius: 50%;
    }
    
    h1, h2, h3, h4 {
        color: #1E293B !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# TITLE & SILENT LOAD DATA
# =====================================================
st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>📊 GoTrans Logistics Executive Dashboard</h1>", unsafe_allow_html=True)

excel_files = glob.glob("data/*.xlsx")
if not excel_files:
    st.error("Excel tidak ditemukan di folder 'data/'.")
    st.stop()

@st.cache_data
def load_data(files):
    all_dfs = []
    for file in files:
        try:
            df = pd.read_excel(file, engine="openpyxl")
            for col in ["Revenue", "Cost", "Rate Vendor", "Add Rate Vendor"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False),
                        errors="coerce"
                    ).fillna(0)

            # Hitung True Cost dengan aman
            if "Cost" in df.columns and "Rate Vendor" in df.columns and "Add Rate Vendor" in df.columns:
                df["True Cost"] = df.apply(lambda row: row["Cost"] if row.get("Cost", 0) > 0 else row.get("Rate Vendor", 0) + row.get("Add Rate Vendor", 0), axis=1)
            elif "Cost" in df.columns:
                df["True Cost"] = df["Cost"]
            else:
                df["True Cost"] = 0

            # Hitung Margin
            if "Revenue" in df.columns:
                df["Margin"] = df["Revenue"] - df["True Cost"]
            else:
                df["Revenue"] = 0
                df["Margin"] = 0

            if "Tgl Order" in df.columns:
                df["Tgl Order"] = pd.to_datetime(df["Tgl Order"], errors="coerce")
                # Bikin kolom Bulan-Tahun buat filter dropdown spesifik
                df['BulanTahun'] = df['Tgl Order'].dt.strftime('%B %Y')
            
            all_dfs.append(df)
        except Exception:
            # SILENT ERROR: Kalau ada file rusak, lewati aja biar UI tetap bersih (ga kuning-kuning)
            pass
            
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

df_full = load_data(excel_files)
if df_full.empty:
    st.error("Data kosong atau format semua file Excel rusak.")
    st.stop()

# =====================================================
# FILTER SUPER: TANGGAL & MULTISELECT CASCADING
# =====================================================
st.markdown("### 🔍 Filter Data")

# Tanggal max dari data untuk acuan "Bulan Berjalan" & "Hari ini"
max_date = df_full["Tgl Order"].dropna().max().date()
min_date = df_full["Tgl Order"].dropna().min().date()

# 1. Row Filter Tanggal
c_preset, c_date = st.columns([1, 4])
with c_preset:
    preset_options = [
        "1 Bulan Terakhir", 
        "Bulan Berjalan", 
        "1 Minggu Terakhir", 
        "2 Minggu Terakhir", 
        "3 Bulan Terakhir", 
        "Pilih Bulan Spesifik", 
        "Custom Range"
    ]
    date_preset = st.selectbox("⏳ Opsi Waktu", preset_options, index=0)

with c_date:
    df_f = df_full.copy()
    
    if date_preset == "1 Minggu Terakhir":
        df_f = df_f[df_f["Tgl Order"].dt.date >= (max_date - datetime.timedelta(days=7))]
        st.info(f"Menampilkan data 7 hari terakhir (sampai {max_date})")
        
    elif date_preset == "2 Minggu Terakhir":
        df_f = df_f[df_f["Tgl Order"].dt.date >= (max_date - datetime.timedelta(days=14))]
        st.info(f"Menampilkan data 14 hari terakhir (sampai {max_date})")
        
    elif date_preset == "Bulan Berjalan":
        df_f = df_f[(df_f["Tgl Order"].dt.year == max_date.year) & (df_f["Tgl Order"].dt.month == max_date.month)]
        st.info(f"Menampilkan data bulan {max_date.strftime('%B %Y')}")
        
    elif date_preset == "1 Bulan Terakhir":
        df_f = df_f[df_f["Tgl Order"].dt.date >= (max_date - datetime.timedelta(days=30))]
        st.info(f"Menampilkan data 30 hari terakhir (sampai {max_date})")
        
    elif date_preset == "3 Bulan Terakhir":
        df_f = df_f[df_f["Tgl Order"].dt.date >= (max_date - datetime.timedelta(days=90))]
        st.info(f"Menampilkan data 90 hari terakhir (sampai {max_date})")
        
    elif date_preset == "Pilih Bulan Spesifik":
        if 'BulanTahun' in df_full.columns:
            list_bulan = df_full['BulanTahun'].dropna().unique().tolist()
            sel_bulan = st.multiselect("🗓️ Pilih Bulan", list_bulan, placeholder="Bisa ceklis lebih dari satu bulan...")
            if sel_bulan:
                df_f = df_f[df_f['BulanTahun'].isin(sel_bulan)]
                
    elif date_preset == "Custom Range":
        d_val = st.date_input("📅 Tentukan Rentang", [max_date - datetime.timedelta(days=30), max_date], min_value=min_date, max_value=max_date)
        if len(d_val) == 2:
            df_f = df_f[(df_f["Tgl Order"].dt.date >= d_val[0]) & (df_f["Tgl Order"].dt.date <= d_val[1])]

# 2. Row Filter Multiselect Cascading (Saling Mengunci Dinamis)
f1, f2, f3, f4, f5 = st.columns(5)

# Fungsi helper buat ngambil opsi
def get_opts(df, col):
    return sorted([str(x) for x in df[col].dropna().unique()]) if col in df.columns else []

with f1:
    opts_client = get_opts(df_f, "Client")
    sel_client = st.multiselect("🏢 Client", opts_client, placeholder="Semua Client")
    if sel_client: df_f = df_f[df_f["Client"].isin(sel_client)]

with f2:
    opts_vendor = get_opts(df_f, "Nama Vendor")
    sel_vendor = st.multiselect("🤝 Vendor", opts_vendor, placeholder="Semua Vendor")
    if sel_vendor: df_f = df_f[df_f["Nama Vendor"].isin(sel_vendor)]

with f3:
    opts_truck = get_opts(df_f, "Tipe Truk")
    sel_truck = st.multiselect("🚚 Truck", opts_truck, placeholder="Semua Truck")
    if sel_truck: df_f = df_f[df_f["Tipe Truk"].isin(sel_truck)]

with f4:
    opts_driver = get_opts(df_f, "Driver")
    sel_driver = st.multiselect("👨‍✈️ Driver", opts_driver, placeholder="Semua Driver")
    if sel_driver: df_f = df_f[df_f["Driver"].isin(sel_driver)]

with f5:
    opts_nopol = get_opts(df_f, "No Polisi")
    sel_nopol = st.multiselect("🚛 Nopol", opts_nopol, placeholder="Semua Nopol")
    if sel_nopol: df_f = df_f[df_f["No Polisi"].isin(sel_nopol)]

# =====================================================
# KPI CARDS
# =====================================================
revenue = df_f["Revenue"].sum()
cost = df_f["True Cost"].sum()
margin = df_f["Margin"].sum()
margin_pct = (margin / revenue * 100 if revenue > 0 else 0)

grp_pct, non_pct = 0, 0
if "Grouping" in df_f.columns and not df_f.empty:
    group_counts = df_f["Grouping"].value_counts(normalize=True) * 100
    grp_pct = group_counts.get("Group", group_counts.iloc[0] if not group_counts.empty else 0)
    non_pct = 100 - grp_pct

st.write("")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"<div class='fin-card'><div class='fin-title'>🚚 Total DO</div><div class='fin-value'>{len(df_f):,}</div></div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='fin-card'>
        <div class='fin-title'>🍩 Group vs Non</div>
        <div class='mini-donut-container' style='background: conic-gradient(#F43F5E 0% {grp_pct}%, #CBD5E1 {grp_pct}% 100%);'>
            <div class='mini-donut-hole'></div>
        </div>
        <div style='font-size: 12px; font-weight: bold; margin-top: 5px;'>
            <span style='color: #F43F5E;'>G: {grp_pct:.1f}%</span> | <span style='color: #94A3B8;'>NG: {non_pct:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"<div class='fin-card'><div class='fin-title'>💰 Revenue</div><div class='fin-value'>Rp {revenue:,.0f}</div></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='fin-card'><div class='fin-title'>💸 Cost</div><div class='fin-value'>Rp {cost:,.0f}</div></div>", unsafe_allow_html=True)
with c5:
    st.markdown(f"<div class='fin-card'><div class='fin-title'>📈 Margin %</div><div class='fin-value'>{margin_pct:.1f}%</div></div>", unsafe_allow_html=True)


# --- LAYOUT PLOTLY DEFAULT ---
layout_defaults = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#1E293B', size=11), 
    xaxis=dict(tickfont=dict(color='#1E293B'), showgrid=False, title=""),
    yaxis=dict(tickfont=dict(color='#1E293B'), gridcolor='#E2E8F0', title="")
)
hbar_layout = dict(margin=dict(l=250, r=20, t=30, b=20), **layout_defaults)

# =====================================================
# ROW 1: REV VS COST & MARGIN
# =====================================================
st.write("---")
g1, g2 = st.columns(2)
daily = df_f.groupby("Tgl Order")[["Revenue", "True Cost"]].sum().reset_index()
daily["Margin"] = daily["Revenue"] - daily["True Cost"]

with g1:
    st.subheader("📉 Revenue vs Cost Trend")
    fig_rev = go.Figure()
    fig_rev.add_scatter(x=daily["Tgl Order"], y=daily["Revenue"], mode="lines+markers", name="Revenue", line=dict(color='#38BDF8', width=3))
    fig_rev.add_scatter(x=daily["Tgl Order"], y=daily["True Cost"], mode="lines+markers", name="Cost", line=dict(color='#F43F5E', width=3))
    fig_rev.update_layout(height=350, hovermode="x unified", **layout_defaults)
    st.plotly_chart(fig_rev, use_container_width=True, theme=None)

with g2:
    st.subheader("📊 Margin Trend")
    fig_mar = go.Figure()
    fig_mar.add_scatter(x=daily["Tgl Order"], y=daily["Margin"], mode="lines+markers", name="Margin", line=dict(color='#10B981', width=3))
    fig_mar.update_layout(height=350, hovermode="x unified", **layout_defaults)
    st.plotly_chart(fig_mar, use_container_width=True, theme=None)

# =====================================================
# ROW 2: TOP 7 CLIENT & TOP 7 PRODUCT 
# =====================================================
st.write("---")
g3, g4 = st.columns(2)

with g3:
    st.subheader("🏢 Top 7 Client")
    top_client = df_f["Client"].value_counts().head(7).reset_index()
    top_client.columns = ["Client", "DO"]
    fig_client = px.bar(top_client, x="DO", y="Client", orientation="h", text="DO", color_discrete_sequence=['#3B82F6'])
    fig_client.update_layout(height=350, **hbar_layout)
    fig_client.update_yaxes(categoryorder="total ascending", automargin=True, title=None)
    st.plotly_chart(fig_client, use_container_width=True, theme=None)

with g4:
    st.subheader("📦 Top 7 Product")
    if "Product" in df_f.columns:
        top_prod = df_f["Product"].value_counts().head(7).reset_index()
        top_prod.columns = ["Product", "DO"]
        fig_prod = px.bar(top_prod, x="DO", y="Product", orientation="h", text="DO", color_discrete_sequence=['#F59E0B'])
        fig_prod.update_layout(height=350, **hbar_layout)
        fig_prod.update_yaxes(categoryorder="total ascending", automargin=True, title=None)
        st.plotly_chart(fig_prod, use_container_width=True, theme=None)
    else:
        st.info("Kolom 'Product' tidak ditemukan di excel.")

# =====================================================
# ROW 3: TOP 7 KOTA & TOP 7 SHIP TO
# =====================================================
st.write("---")
g5, g6 = st.columns(2)

with g5:
    st.subheader("📍 Top 7 Kota Tujuan")
    top_kota = df_f["kota.1"].value_counts().head(7).reset_index()
    top_kota.columns = ["Kota", "DO"]
    fig_kota = px.bar(top_kota, x="DO", y="Kota", orientation="h", text="DO", color_discrete_sequence=['#8B5CF6'])
    fig_kota.update_layout(height=350, **hbar_layout)
    fig_kota.update_yaxes(categoryorder="total ascending", automargin=True, title=None)
    st.plotly_chart(fig_kota, use_container_width=True, theme=None)

with g6:
    st.subheader("🎯 Top 7 Ship To")
    top_ship = df_f["Ship To"].value_counts().head(7).reset_index()
    top_ship.columns = ["Ship To", "DO"]
    fig_ship = px.bar(top_ship, x="DO", y="Ship To", orientation="h", text="DO", color_discrete_sequence=['#EC4899'])
    fig_ship.update_layout(height=350, **hbar_layout)
    fig_ship.update_yaxes(categoryorder="total ascending", automargin=True, title=None)
    st.plotly_chart(fig_ship, use_container_width=True, theme=None)

# =====================================================
# ROW 4: TRUCK TYPE & EXECUTIVE INSIGHT
# =====================================================
st.write("---")
g7, g8 = st.columns(2)

with g7:
    st.subheader("🚛 Top 7 Truck Type")
    top_truck = df_f["Tipe Truk"].value_counts().head(7).reset_index()
    top_truck.columns = ["Truck", "DO"]
    fig_truck = px.bar(top_truck, x="DO", y="Truck", orientation="h", text="DO", color_discrete_sequence=['#14B8A6'])
    fig_truck.update_layout(height=350, **hbar_layout)
    fig_truck.update_yaxes(categoryorder="total ascending", automargin=True, title=None)
    st.plotly_chart(fig_truck, use_container_width=True, theme=None)

with g8:
    st.subheader("💡 Executive Insight")
    if not df_f.empty:
        top_client_val = df_f["Client"].value_counts()
        top_city_val = df_f["kota.1"].value_counts()
        st.success(f"""
        **📌 Rangkuman Eksekutif (Sesuai Filter):**
        * **🏢 Client Teratas:** {top_client_val.index[0] if not top_client_val.empty else '-'} ({top_client_val.iloc[0] if not top_client_val.empty else 0} DO)
        * **📍 Kota Utama:** {top_city_val.index[0] if not top_city_val.empty else '-'}
        * **💰 Total Revenue:** Rp {revenue:,.0f}
        * **📈 Margin Bersih:** Rp {margin:,.0f} ({margin_pct:.1f}%)
        """)
    else:
        st.warning("Data kosong berdasarkan filter yang dipilih.")

# =====================================================
# PEMBUATAN DATA CLEAN EXPORT
# =====================================================
export_mapping = {
    "Tgl Order": "Tgl Order",
    "No Order": "No Order", 
    "No Polisi": "Nopol",
    "Driver": "Driver",
    "Tipe Truk": "Tipe Truk",
    "Client": "Client",
    "Nama Vendor": "Vendor",
    "kota.1": "Kota Tujuan",
    "Ship To": "Ship To",
    "Kategori Produk": "Kategori Produk",
    "Revenue": "Revenue",
    "True Cost": "Cost",
    "Margin": "Margin"
}

avail_cols = {k: v for k, v in export_mapping.items() if k in df_f.columns}
df_export = df_f[list(avail_cols.keys())].copy()
df_export.rename(columns=avail_cols, inplace=True)

if "Tgl Order" in df_export.columns:
    df_export["Tgl Order"] = df_export["Tgl Order"].dt.strftime('%Y-%m-%d')

# =====================================================
# BAGIAN RAW DATA & EXPORT
# =====================================================
st.write("---")
st.markdown("### 📥 Menu Unduhan Data & Report")

def create_utilisasi_report(df):
    df_util = df.copy()
    start_date, end_date = df_util["Tgl Order"].min(), df_util["Tgl Order"].max()
    
    holidays_2025 = pd.to_datetime(['2025-01-01', '2025-01-27', '2025-01-28', '2025-01-29', '2025-03-28', '2025-03-29', '2025-03-31', '2025-04-01', '2025-04-02', '2025-04-03', '2025-04-04', '2025-04-07', '2025-04-18', '2025-05-01', '2025-05-12', '2025-05-13', '2025-05-29', '2025-05-30', '2025-06-06', '2025-06-09', '2025-06-27', '2025-08-17', '2025-08-18', '2025-09-05', '2025-12-25', '2025-12-26']).date
    
    work_days = sum(1 for d in pd.date_range(start_date, end_date) if d.weekday() != 6 and d.date() not in holidays_2025) if pd.notnull(start_date) else 25
    if work_days == 0: work_days = 25 
        
    if "Nama Transporter" in df_util.columns: df_util = df_util[df_util["Nama Transporter"] == "GoTrans Logistics International"]
    if "Status Pengiriman" in df_util.columns: df_util = df_util[~df_util["Status Pengiriman"].isin(["Cancel Order Approved", "Not Accepted", "Cancel Order Requested"])]
        
    df_util["Work day"] = work_days
    pivot_cols = {k: v for k, v in [("Work day", "mean"), ("No Order", "count"), ("Total MRC", "sum"), ("Revenue", "sum")] if k in df_util.columns}
    if "Total MRC" in df_util.columns: df_util["Total MRC"] = pd.to_numeric(df_util["Total MRC"], errors="coerce").fillna(0)
    
    idx = [col for col in ["No Polisi", "Definition"] if col in df_util.columns]
    if idx and pivot_cols:
        pivot = pd.pivot_table(df_util, index=idx, aggfunc=pivot_cols)
        if "No Order" in pivot.columns: pivot.rename(columns={"No Order": "Ritase"}, inplace=True)
        pivot = pivot[[c for c in ["Work day", "Ritase", "Total MRC", "Revenue"] if c in pivot.columns]]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pivot.to_excel(writer, sheet_name='PivotUtilisasi')
        return output.getvalue()
    return None

col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    output_filtered = io.BytesIO()
    with pd.ExcelWriter(output_filtered, engine='openpyxl') as writer: 
        df_export.to_excel(writer, index=False, sheet_name='CleanedData')
        
    st.download_button(
        label="📥 Download Data Filter Dashboard (Rapi)", 
        data=output_filtered.getvalue(), 
        file_name="Dashboard_GoTrans_Data.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        use_container_width=True
    )

with col_dl2:
    utilisasi_excel = create_utilisasi_report(df_full) 
    if utilisasi_excel: 
        st.download_button(
            label="📊 Download Report Utilisasi Armada (Format Pivot)", 
            data=utilisasi_excel, 
            file_name="Report_Utilisasi_Armada.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            use_container_width=True
        )
    else: 
        st.button("📊 Report Utilisasi (Kolom Tidak Lengkap)", disabled=True, use_container_width=True)

st.write("---")
st.markdown("### 📄 Tabel Data (Versi Rapi)")
st.dataframe(df_export, use_container_width=True, hide_index=True)