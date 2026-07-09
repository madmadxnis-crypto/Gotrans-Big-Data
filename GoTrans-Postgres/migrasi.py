import pandas as pd
from sqlalchemy import create_engine, text
import glob
import os

# Mengambil URL database dari GitHub Secrets secara otomatis
DATABASE_URL = os.getenv("SUPABASE_URL", "").strip()
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
                print(f"Menggunakan metode Update & Insert (Zero Egress) untuk '{table_name}'...", flush=True)
                
                # 1. Ambil daftar No_Order dari file Excel
                # Hapus baris yang No_Order-nya kosong (NaN/NaT) dari dataframe biar query gak error
                df = df.dropna(subset=[kolom_unik])
                excel_ids = df[kolom_unik].astype(str).tolist()
                
                try:
                    # 2. Hapus data lama di Supabase yang No_Order-nya ada di file Excel ini (Zero Egress)
                    if excel_ids:
                        # Format list menjadi string dan escape tanda kutip tunggal jika ada ('ORDER1', 'ORDER2')
                        safe_ids = [str(eid).replace("'", "''") for eid in excel_ids]
                        format_ids = "', '".join(safe_ids)
                        
                        delete_query = text(f"""DELETE FROM "{table_name}" WHERE "{kolom_unik}" IN ('{format_ids}')""")
                        
                        # Jalankan perintah DELETE
                        with engine.begin() as conn:
                            conn.execute(delete_query)
                            
                    # 3. Masukkan semua data dari Excel sebagai data terbaru (Append)
                    if not df.empty:
                        df.to_sql(
                            table_name, 
                            engine, 
                            if_exists='append', 
                            index=False, 
                            chunksize=1000, 
                            method='multi'
                        )
                        print(f"Sukses update & upload {len(df)} baris data ke tabel: {table_name}!", flush=True)
                    
                except Exception as e:
                    # Kalau error (misal tabel belum ada di Supabase), langsung buat tabel baru dan upload
                    print(f"Tabel '{table_name}' sepertinya belum ada (atau ada error: {e}). Membuat tabel baru...", flush=True)
                    if not df.empty:
                        df.to_sql(
                            table_name, 
                            engine, 
                            if_exists='append', 
                            index=False, 
                            chunksize=1000, 
                            method='multi'
                        )
                        print(f"Sukses membuat tabel dan upload data ke: {table_name}!", flush=True)
            
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
