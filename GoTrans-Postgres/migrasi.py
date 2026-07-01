import pandas as pd
from sqlalchemy import create_engine
import glob
import os

# Mengambil URL database dari GitHub Secrets secara otomatis
DATABASE_URL = os.getenv("SUPABASE_URL")
if not DATABASE_URL:
    raise ValueError("Waduh, SUPABASE_URL nggak ketemu di GitHub Secrets!")

engine = create_engine(DATABASE_URL)

def migrate():
    # Sesuaikan path folder data lu di GitHub
    path = "GoTrans-Postgres/data/*.xlsx"
    excel_files = glob.glob(path)
    
    print(f"Mencari file di: {path}")
    print(f"Menemukan {len(excel_files)} file untuk dimigrasi.")
    
    for file in excel_files:
        print(f"--- Sedang memproses: {file} ---")
        df = pd.read_excel(file, engine="openpyxl")
        
        # Bersihkan spasi dan titik di nama kolom biar PostgreSQL nggak error
        df.columns = [c.replace(' ', '_').replace('.', '_') for c in df.columns]
        
        # Ambil nama file tanpa ekstensi untuk jadi nama tabel
        table_name = os.path.basename(file).replace('.xlsx', '')
        
        # Kirim ke Supabase
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Sukses upload tabel: {table_name}!")

if __name__ == "__main__":
    migrate()
