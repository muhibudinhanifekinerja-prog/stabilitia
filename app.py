import streamlit as st
from supabase import create_client, Client
import pandas as pd
import google.generativeai as genai

# ==========================================
# 1. KONFIGURASI UI/UX STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Chatbot Analisis Ekonomi",
    page_icon="📈",
    layout="centered"
)

# Custom CSS untuk UI yang lebih modern
st.markdown("""
<style>
    .stChatMessage { border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    .stChatMessage.user { background-color: #e6f2ff; }
    .stChatMessage.assistant { background-color: #f0f2f6; }
    h1 { color: #1E3A8A; font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Chatbot Analisis Harga & Inflasi")
st.caption("Tanyakan seputar data harga komoditas harian, pasar, dan tingkat inflasi wilayah.")

# ==========================================
# 2. KONEKSI SUPABASE
# ==========================================
SUPABASE_URL = "https://hkllhgmfbnepgtfnrxuj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhrbGxoZ21mYm5lcGd0Zm5yeHVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcxOTA1NzQsImV4cCI6MjA4Mjc2NjU3NH0.Ft8giYKJIPPiGstRJXJNb_uuKQUuNlaAM8p2dE2UKs0"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ==========================================
# 3. KONEKSI AI (Untuk Respon Manusia)
# ==========================================
# Masukkan API Key Gemini Anda di sini (Dapatkan gratis di Google AI Studio)
GEMINI_API_KEY = "AIzaSyA4fceuUeaC0l-97hxKNXdaF398-QGSU5U" 

if GEMINI_API_KEY != " ":
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("⚠️ API Key LLM belum diisi. Chatbot akan menggunakan respon statis sementara.")

# Skema Database sebagai Konteks AI
DB_SCHEMA_CONTEXT = """
Kamu adalah AI Data Analyst Ekonomi yang ahli. Kamu memiliki akses ke database dengan skema berikut:
1. Tabel 'inflasi': id_inflasi, tahun, bulan, level_wilayah, nama_wilayah, inflasi_mtm, inflasi_ytd, inflasi_yoy, created_at
2. Tabel 'harga_harian': tanggal, id_komoditas, id_pasar, harga
3. Tabel 'komoditas': id_komoditas, nama_komoditas, satuan
4. Tabel 'pasar': id_pasar, nama_pasar, kabupaten, kecamatan

Gunakan bahasa yang ramah, profesional, dan analitis seperti seorang konsultan ekonomi.
"""

# ==========================================
# 4. LOGIKA CHATBOT & DATABASE
# ==========================================
# Inisialisasi riwayat chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo! Saya adalah Asisten Analisis Ekonomi Anda. Ada yang bisa saya bantu terkait data inflasi atau harga komoditas hari ini?"}
    ]

# Tampilkan riwayat chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input pengguna
if prompt := st.chat_input("Contoh: Berapa harga rata-rata beras hari ini?"):
    # Tampilkan pesan user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Tampilkan respon asisten
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Skenario 1: Jika user bertanya tentang data (Contoh: Tarik data dari Supabase)
        # Note: Dalam aplikasi production, AI bisa merancang SQL query lalu mengeksekusinya. 
        # Di sini kita memberikan contoh penarikan data komoditas dasar untuk memperkaya konteks AI.
        try:
            # Contoh penarikan data (Bisa disesuaikan berdasarkan intent user)
            res_komoditas = supabase.table("komoditas").select("*").limit(5).execute()
            data_konteks = f"Data sampel komoditas: {res_komoditas.data}"
            
            # Gabungkan prompt user dengan konteks schema & data
            full_prompt = f"{DB_SCHEMA_CONTEXT}\n\nKonteks Data Tambahan: {data_konteks}\n\nPertanyaan Pengguna: {prompt}\n\nBerikan jawaban analitis berdasarkan skema dan data tersebut:"
            
            if GEMINI_API_KEY != "":
                response = model.generate_content(full_prompt)
                full_response = response.text
            else:
                full_response = "Maaf, API Key LLM belum dikonfigurasi. Namun saya dapat menerima pertanyaan Anda: " + prompt
                
        except Exception as e:
            full_response = f"Mohon maaf, terjadi kesalahan saat menghubungi database: {e}"

        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
