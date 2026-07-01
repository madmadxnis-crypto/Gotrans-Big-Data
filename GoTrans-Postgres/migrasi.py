import pandas as pd
from sqlalchemy import create_engine
import glob
import os

DATABASE_URL = "postgresql://postgres:[Y$zP8#YN&tr&hZj]@db.ycrrjjgrmdvwenrqfvlk.supabase.co:5432/postgres"
engine = create_engine(DATABASE_URL)

def migrate():
    # Pastikan lokasi folder benar
    path = "data/*.xlsx"
    excel_files = glob.glob(path)
    
    print(f"Mencari file di: {os.getcwd()}/data/")
    print(f"Ketemu {len(excel_files)} file: {excel_files}")
    
    if len(excel_files) == 0:
        print("Waduh, nggak ada file Excel ketemu di folder data!")
        return

    for file in excel_files:
        print(f"--- Sedang memproses: {file} ---")
        df = pd.read_excel(file, engine="openpyxl")
        df.columns = [c.replace(' ', '_').replace('.', '_') for c in df.columns]
        table_name = os.path.basename(file).replace('.xlsx', '')
        
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Sukses upload {table_name}!")

if __name__ == "__main__":
    migrate()