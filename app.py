import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import pandas as pd

# ==========================================
# 1. KONFIGURASI UI/UX MODERN & RESPONSIF
# ==========================================
st.set_page_config(
    page_title="Asisten Data Ekonomi Pekalongan",
    page_icon="📉",
    layout="centered"
)

# Custom CSS untuk tampilan profesional
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; padding: 15px; margin-bottom: 12px; }
    .stChatMessage.user { background-color: #f0f7ff; border: 1px solid #d1e3ff; }
    .stChatMessage.assistant { background-color: #ffffff; border: 1px solid #eaeaea; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .main { background-color: #f9fbff; }
    h1 { color: #1e3a8a; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Chatbot Analisis Ekonomi")
st.caption("Monitoring Harga Komoditas & Analisis Inflasi Kabupaten Pekalongan")

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
# 3. KONEKSI AI (DENGAN SECURITY & AUTO-DETECTION)
# ==========================================
# Mengambil API Key secara aman dari Streamlit Secrets
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        GEMINI_API_KEY = ""
except:
    GEMINI_API_KEY = ""

model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Auto-deteksi model yang tersedia untuk menghindari Error 404
    try:
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if model_list:
            # Mengutamakan gemini-1.5-flash jika tersedia, jika tidak ambil yang pertama
            selected_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in model_list else model_list[0]
            model = genai.GenerativeModel(selected_model)
    except Exception as e:
        st.error(f"Gagal memuat model AI: {e}")
else:
    st.info("💡 Hubungkan API Key di 'Streamlit Secrets' untuk mengaktifkan respon cerdas.")

# Instruksi sistem untuk AI
SYSTEM_PROMPT = """
Kamu adalah pakar data ekonomi dari Kabupaten Pekalongan. Kamu membantu Tim Pengendalian Inflasi Daerah (TPID).
Karakteristik jawabanmu:
- Menggunakan bahasa yang ramah, manusiawi, dan profesional.
- Memahami terminologi seperti 'optimasi lahan' dan 'tambah tanam' dalam konteks pertanian daerah.
- Fokus pada analisis data dari tabel: inflasi, harga_harian, komoditas, dan pasar.
- Selalu berusaha memberikan insight statistik (seperti rata-rata atau tren) jika diminta.
"""

# ==========================================
# 4. LOGIKA INTERAKSI CHAT
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo! Saya siap membantu menganalisis data harga komoditas dan inflasi. Apa yang ingin Anda ketahui hari ini?"}
    ]

# Tampilkan riwayat pesan
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input pengguna menggunakan Walrus Operator
if prompt := st.chat_input("Tanyakan sesuatu (contoh: Bagaimana tren harga hari ini?)"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # Penarikan data pendukung dari Supabase untuk memperkaya konteks AI
            context_data = ""
            try:
                res = supabase.table("komoditas").select("nama_komoditas").limit(5).execute()
                context_data = f"Komoditas tersedia: {[d['nama_komoditas'] for d in res.data]}"
            except:
                pass

            if model:
                full_query = f"{SYSTEM_PROMPT}\n\nKonteks Database: {context_data}\n\nPertanyaan User: {prompt}"
                response = model.generate_content(full_query)
                full_response = response.text
            else:
                full_response = "Bot berjalan dalam mode terbatas. Mohon atur GEMINI_API_KEY di pengaturan Secrets Streamlit Anda."

        except Exception as e:
            full_response = f"Terjadi kendala teknis: {str(e)}"
        
        placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
