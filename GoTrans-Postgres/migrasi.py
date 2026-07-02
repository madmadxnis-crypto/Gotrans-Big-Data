import pandas as pd
from sqlalchemy import create_engine
import glob
import os

# Mengambil URL database dari GitHub Secrets secara otomatis
DATABASE_URL = os.getenv("SUPABASE_URL").strip()
if not DATABASE_URL:
    raise ValueError("Waduh, SUPABASE_URL nggak ketemu di GitHub Secrets!")

# Tambahkan connect_args untuk timeout, agar kalau gagal konek langsung error, nggak hang
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})

def migrate():
    # Sesuaikan path folder data di GitHub
    path = "GoTrans-Postgres/data/*.xlsx"
    excel_files = glob.glob(path)
    
    # Tambahkan flush=True agar log langsung dipaksa tampil di GitHub Actions
    print(f"Mencari file di: {path}", flush=True)
    print(f"Menemukan {len(excel_files)} file untuk dimigrasi.", flush=True)
    
    for file in excel_files:
        print(f"--- Sedang memproses: {file} ---", flush=True)
        try:
            df = pd.read_excel(file, engine="openpyxl")
            print(f"Berhasil membaca file Excel. Total baris di file: {len(df)}", flush=True)
            
            # Bersihkan spasi dan titik di nama kolom menjadi underscore
            df.columns = [str(c).replace(' ', '_').replace('.', '_') for c in df.columns]
            
            # Ambil nama file tanpa ekstensi untuk jadi nama tabel
            table_name = os.path.basename(file).replace('.xlsx', '')
            
            # Kolom unik sudah di-set ke No Order (dengan underscore)
            kolom_unik = 'No_Order' 
            
            if kolom_unik in df.columns:
                # 1. Cek ID apa saja yang sudah ada di database Supabase
                try:
                    # Kutip ganda ditambahkan agar PostgreSQL aman membaca nama kolom/tabel
                    query = f'SELECT "{kolom_unik}" FROM "{table_name}"'
                    existing_data = pd.read_sql(query, engine)
                    existing_ids = existing_data[kolom_unik].tolist()
                except Exception as e:
                    # Kalau error (misal tabel belum pernah dibuat di DB), anggap database masih kosong
                    print(f"Tabel '{table_name}' sepertinya baru atau belum ada. Membuat tabel baru...", flush=True)
                    existing_ids = []
                
                # 2. Saring data Excel. Hanya simpan baris yang ID-nya BELUM ADA di database
                df_baru = df[~df[kolom_unik].isin(existing_ids)]
                
                # 3. Upload hanya jika ada data baru (menggunakan append)
                if not df_baru.empty:
                    print(f"Menemukan {len(df_baru)} baris data BARU. Mulai upload...", flush=True)
                    df_baru.to_sql(
                        table_name, 
                        engine, 
                        if_exists='append', 
                        index=False, 
                        chunksize=1000, 
                        method='multi'
                    )
                    print(f"Sukses upload data baru ke tabel: {table_name}!", flush=True)
                else:
                    print(f"Semua data dari file ini sudah ada di database. Lewati upload.", flush=True)
            
            else:
                # Fallback: Kalau kolom unik tidak ditemukan di file Excel ini, pakai cara replace
                print(f"⚠️ Peringatan: Kolom '{kolom_unik}' tidak ditemukan di file ini!", flush=True)
                print(f"Menggunakan metode REPLACE untuk tabel '{table_name}'...", flush=True)
                df.to_sql(
                    table_name, 
                    engine, 
                    if_exists='replace', 
                    index=False, 
                    chunksize=1000, 
                    method='multi'
                )
                print(f"Sukses REPLACE tabel: {table_name}!", flush=True)

        except Exception as e:
            print(f"ERROR saat memproses {file}: {e}", flush=True)

if __name__ == "__main__":
    migrate()
