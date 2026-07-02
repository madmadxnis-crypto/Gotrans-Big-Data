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
    # Sesuaikan path folder data lu di GitHub
    path = "GoTrans-Postgres/data/*.xlsx"
    excel_files = glob.glob(path)
    
    # Tambahkan flush=True agar log langsung dipaksa tampil di GitHub Actions
    print(f"Mencari file di: {path}", flush=True)
    print(f"Menemukan {len(excel_files)} file untuk dimigrasi.", flush=True)
    
    for file in excel_files:
        print(f"--- Sedang memproses: {file} ---", flush=True)
        try:
            df = pd.read_excel(file, engine="openpyxl")
            print(f"Berhasil membaca file Excel. Total baris: {len(df)}", flush=True)
            
            # Bersihkan spasi dan titik di nama kolom
            df.columns = [str(c).replace(' ', '_').replace('.', '_') for c in df.columns]
            
            # Ambil nama file tanpa ekstensi untuk jadi nama tabel
            table_name = os.path.basename(file).replace('.xlsx', '')
            
            print(f"Mengirim data ke tabel '{table_name}' di Supabase...", flush=True)
            
            # PERBAIKAN UTAMA: Tambahkan chunksize dan method='multi'
            df.to_sql(
                table_name, 
                engine, 
                if_exists='replace', 
                index=False, 
                chunksize=1000,   # Kirim per 1000 baris
                method='multi'    # Optimasi bulk insert PostgreSQL
            )
            print(f"Sukses upload tabel: {table_name}!", flush=True)
            
        except Exception as e:
            print(f"ERROR saat memproses {file}: {e}", flush=True)

if __name__ == "__main__":
    migrate()
