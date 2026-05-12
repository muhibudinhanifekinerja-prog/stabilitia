import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai

# ==========================================
# 1. KONFIGURASI UI/UX STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Chatbot Analisis Ekonomi",
    page_icon="📈",
    layout="centered"
)

# Custom CSS untuk UI modern
st.markdown("""
<style>
    .stChatMessage { border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    .stChatMessage.user { background-color: #e6f2ff; }
    .stChatMessage.assistant { background-color: #f0f2f6; }
    h1 { color: #1E3A8A; font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Chatbot Analisis Harga & Inflasi")
st.caption("Tanyakan seputar data harga komoditas harian, pergerakan pasar, dan tingkat inflasi wilayah.")

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
# 3. KONEKSI AI & AUTO-DETEKSI MODEL
# ==========================================
# PENTING: Masukkan API Key Gemini Anda di antara tanda kutip di bawah ini!
GEMINI_API_KEY = "AIzaSyA4fceuUeaC0l-97hxKNXdaF398-QGSU5U"

model = None
if GEMINI_API_KEY != "":
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Auto-mencari model yang didukung oleh API Key Anda agar tidak error 404
    try:
        model_aktif = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_aktif = m.name
                break 
        
        if model_aktif:
            model = genai.GenerativeModel(model_aktif)
        else:
            st.error("API Key valid, tapi tidak memiliki akses ke model teks apapun.")
    except Exception as e:
        st.error(f"Error saat menghubungi Google AI: {e}")
else:
    st.warning("⚠️ API Key LLM belum diisi. Chatbot menggunakan mode respons statis sementara.")

# Skema Database sebagai Konteks AI (Otak Chatbot)
DB_SCHEMA_CONTEXT = """
Kamu adalah AI Data Analyst Ekonomi andalan Tim Pengendalian Inflasi Daerah (TPID) di Kabupaten Pekalongan.
Tugas utamamu adalah membantu menganalisis stabilitas harga komoditas bapokting (bahan pokok dan penting) serta laju inflasi daerah.

Kamu memiliki akses ke database dengan skema berikut:
1. Tabel 'inflasi': id_inflasi, tahun, bulan, level_wilayah, nama_wilayah, inflasi_mtm, inflasi_ytd, inflasi_yoy, created_at
2. Tabel 'harga_harian': tanggal, id_komoditas, id_pasar, harga
3. Tabel 'komoditas': id_komoditas, nama_komoditas, satuan
4. Tabel 'pasar': id_pasar, nama_pasar, kabupaten, kecamatan

Gunakan bahasa yang profesional, akurat, dan solutif. Jika ditanya tentang pergerakan harga, asumsikan kamu dapat mengkorelasikannya dengan data wilayah.
"""

# ==========================================
# 4. LOGIKA CHATBOT
# ==========================================
# Inisialisasi riwayat chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo! Saya adalah Asisten Analisis Ekonomi Anda. Ada yang bisa saya bantu terkait pemantauan harga komoditas pasar atau data inflasi hari ini?"}
    ]

# Tampilkan riwayat chat sebelumnya
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input teks pengguna dengan walrus operator (:=)
if prompt := st.chat_input("Contoh: Berapa harga rata-rata beras hari ini?"):
    
    # Tampilkan pesan user ke layar
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Proses respon asisten
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Mengambil sedikit sampel data komoditas dari Supabase sebagai pelengkap memori AI
            res_komoditas = supabase.table("komoditas").select("nama_komoditas, satuan").limit(5).execute()
            data_konteks = f"Sampel data komoditas di sistem: {res_komoditas.data}"
            
            # Menggabungkan seluruh instruksi, konteks, dan pertanyaan
            full_prompt = f"{DB_SCHEMA_CONTEXT}\n\nKonteks Data: {data_konteks}\n\nPertanyaan Pengguna: {prompt}\n\nBerikan jawaban analitis:"
            
            # Pengecekan apakah model AI siap digunakan
            if model is not None:
                response = model.generate_content(full_prompt)
                full_response = response.text
            else:
                full_response = f"(Mode Terbatas) Anda bertanya: {prompt} \n\n*Catatan: Bot belum bisa menjawab seperti manusia karena API Key belum diisi.*"
                
        except Exception as e:
            full_response = f"Mohon maaf, terjadi kesalahan pada sistem saat memproses data: {e}"

        # Tampilkan balasan ke layar dan simpan ke riwayat
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
