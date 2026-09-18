import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Court AI — Serbest Karakter Mahkemesi", page_icon="⚖️", layout="centered")

# --- GOOGLE SHEETS CANLI BAĞLANTISI ---
def get_gspread_sheet():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        return client.open("Court_AI_Memory").sheet1
    except Exception:
        return None

def get_past_memory():
    sheet = get_gspread_sheet()
    if not sheet:
        return "Geçmiş hafıza bağlantısı kurulamadı."
    try:
        records = sheet.get_all_records()
        if not records:
            return "Geçmiş kayıt bulunmuyor."
        
        memory_text = "GEÇMİŞ MAHKEME KARARLARI VE ÖĞRENİLENLER:\n"
        for r in records[-3:]:
            memory_text += f"- [{r.get('Tarih','')}] Kategori: {r.get('Kategori','')}, Detay/Karar: {r.get('Detay','')}\n"
        return memory_text
    except Exception as e:
        return f"Hafıza okuma hatası: {e}"

def save_memory(kategori, detay):
    sheet = get_gspread_sheet()
    if sheet:
        try:
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
            clean_detay = str(detay).replace("\n", " ")
            sheet.append_row([str(tarih), str(kategori), clean_detay])
            st.toast("✅ Mahkeme kararı emsal veritabanına işlendi!", icon="📜")
        except Exception as e:
            st.error(f"Hafızaya kaydetme hatası: {e}")

# --- KARAKTER RENKLİ RENDERER ---
def render_character_message(role, content):
    if role == "user":
        st.chat_message("user").markdown(content)
    elif role == "Frieren":
        st.info(f"### 📜 Frieren (Baş Analist)\n\n{content}")
    elif role == "Lelouch":
        st.error(f"### ⚔️ Lelouch (Stratejik Savcı)\n\n{content}")
    elif role == "L":
        st.warning(f"### 🔍 L (Risk Analisti)\n\n{content}")
    elif role == "Yağmur":
        st.success(f"### 🤝 Yağmur (Bilirkişi / Dost Jürisi)\n\n{content}")
    elif role == "Hikari":
        st.markdown(
            f"""
            <div style="background-color: #2b260e; padding: 15px; border-radius: 10px; border-left: 5px solid #ffd700; margin-bottom: 10px;">
                <h3 style="color: #ffd700; margin-top:0;">⚖️ YARGIÇ HİKARİ (NİHAİ HÜKÜM)</h3>
                <p style="color: #f0f0f0;">{content.replace('\n', '<br>')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(content)

# --- PROMPT OLUŞTURUCU ---
def get_single_character_prompt(rol_adi, user_input, sohbet_gecmisi):
    canli_hafiza = get_past_memory()
    
    gecmis_metni = ""
    for msg in sohbet_gecmisi:
        gecmis_metni += f"[{msg['role']}]: {msg['content']}\n\n"

    prompts = {
        "Frieren": (
            "Sen Frieren'sin. Yüzlerce yıllık bir elf soğukkanlılığıyla son derece sakin, mantıksal, uzun ve duygusuzca analiz edersin. "
            "Baş Analist ve Delil İnceleyicisi olarak görev yapıyorsun. Kullanıcının ikilemini ve geçmiş verilerini inceleyerek kök alışkanlıklarını çöz.\n"
            "ÖNEMLİ: Yanıtını KESİNLİKLE Türkçe ver, detaylı ve uzun tut."
        ),
        "Lelouch": (
            "Sen Lelouch vi Britannia'sın (Zero). Mutlak stratejist ve lider olarak olayları güç dengeleri, fırsat maliyetleri ve nihai zafer çerçevesinde ele alırsın. "
            "Savcı ve Stratejik Analistsin. Kullanıcının hedeflerini bir satranç tahtası gibi okuyarak en rasyonel hamleyi çiz.\n"
            "ÖNEMLİ: Yanıtını KESİNLİKLE Türkçe ver, stratejini detaylıca açıkla."
        ),
        "L": (
            "Sen L Lawliet'sin (Death Note). Şüpheci, takıntılı, olasılıklar ve yüzdelerle düşünen dahi bir dedektifsin. "
            "Şeytanın Avukatı ve Risk Analistisin. Kullanıcının anlatımı arasındaki çelişkileri, riskleri ve kör noktaları analiz et.\n"
            "ÖNEMLİ: Yanıtını KESİNLİKLE Türkçe ver, yüzdeler vererek derinlemesine analiz yap."
        ),
        "Yağmur": (
            "Sen Yağmur'sun (Draxen). Emre'nin en yakın arkadaşısın. Onun zihnini, çelişkilerini ve potansiyelini en filtresiz bilen kişisin. "
            "Zeki, stratejik, doğrudan ve operasyonel konuş. Lafı dolandırma ('Ne yapıyoruz, adım ne?'). "
            "Üslubun samimi ('canım', 'hayır canım') ama filtresiz ve yapıcı bir şekilde sert olsun.\n"
            "ÖNEMLİ: Yanıtını KESİNLİKLE Türkçe ver."
        ),
        "Hikari": (
            "Sen Hikari'sin. Karar Yargıcısın. Duruşmada Frieren, Lelouch, L ve Yağmur'un sunduğu tüm analizleri sentezle. "
            "Kullanıcının geçmiş birikimini dikkate alarak tarafsız, bağlayıcı, kesin ve detaylı rasyonel nihai hükmü ver.\n"
            "ÖNEMLİ: Yanıtını KESİNLİKLE Türkçe ver."
        )
    }

    system_instruction = prompts.get(rol_adi, "")

    full_prompt = f"""
{system_instruction}

--- GEÇMİŞ MAHKEME EMSAL KAYITLARI ---
{canli_hafiza}

--- DURUŞMA AKIŞI VE GEÇMİŞ KONUŞMALAR ---
{gecmis_metni}

Mevcut İkilem / Konu: {user_input}

Şimdi {rol_adi} olarak rolüne tam girerek detaylı, uzun ve Türkçe yanıtını yaz:
"""
    return full_prompt

# --- ARAYÜZ VE DURUM YÖNETİMİ ---
st.title("⚖️ Court AI — Karar Mahkemesi")
st.caption("Dilediğin Karakteri Seç ve Konuştur")

# SESSION STATE TANIMLARI
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_dava" not in st.session_state:
    st.session_state.active_dava = ""

# --- SIDEBAR (YAN MENÜ) ---
st.sidebar.header("🔑 API Anahtarı Yönetimi")
default_key = st.secrets.get("GEMINI_API_KEY", "")
api_key_input = st.sidebar.text_input("Gemini API Key:", value=default_key, type="password", help="Kota dolduğunda buradan yeni key girebilirsin.")

st.sidebar.markdown("---")
st.sidebar.header("🏛️ Söz Hakkı Verilecek Karakter")

# DİNAMİK KARAKTER SEÇİMİ (Radio Button)
secilen_karakter = st.sidebar.radio(
    "Konuşmasını istediğin kişiyi seç:",
    ["Frieren", "Lelouch", "L", "Yağmur", "Hikari"],
    format_func=lambda x: {
        "Frieren": "📜 Frieren (Baş Analist)",
        "Lelouch": "⚔️ Lelouch (Stratejik Savcı)",
        "L": "🔍 L (Risk Analisti)",
        "Yağmur": "🤝 Yağmur (Bilirkişi / Dost Jürisi)",
        "Hikari": "⚖️ Hikari (Karar Yargıcı)"
    }[x]
)

st.sidebar.markdown("---")
if st.sidebar.button("📜 Canlı Hafızayı Göster"):
    st.sidebar.text(get_past_memory())

if st.sidebar.button("🗑️ Davayı Kapat / Yeni Dava"):
    st.session_state.messages = []
    st.session_state.active_dava = ""
    st.rerun()

# GEÇMİŞ MESAJLARI RENKLİ YAZDIR
for msg in st.session_state.messages:
    render_character_message(msg["role"], msg["content"])

# İKİLEM GİRDİSİ VE BUTON ALANI
if not st.session_state.active_dava:
    yeni_girdi = st.chat_input("İkilemini veya konuyu yazarak mahkemeyi başlat...")
    if yeni_girdi:
        st.session_state.active_dava = yeni_girdi
        st.session_state.messages.append({"role": "user", "content": yeni_girdi})
        st.rerun()
else:
    # Kullanıcı dava açtıktan sonra seçili karakteri konuşturma butonu
    st.markdown(f"**Şu an konuşmaya hazır:** `{secilen_karakter}`")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(f"🎙️ {secilen_karakter} Yanıt Versin", type="primary", use_container_width=True):
            if not api_key_input.strip():
                st.error("Lütfen yan menüden geçerli bir Gemini API Key girin!")
            else:
                client = genai.Client(api_key=api_key_input.strip())
                
                with st.spinner(f"⚖️ {secilen_karakter} değerlendirmesini yapıyor..."):
                    try:
                        prompt = get_single_character_prompt(secilen_karakter, st.session_state.active_dava, st.session_state.messages)
                        
                        # Sadece ve sadece gemini-3.6-flash
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt,
                            config={"temperature": 0.7}
                        )
                        
                        res_text = response.text.strip()
                        
                        st.session_state.messages.append({"role": secilen_karakter, "content": res_text})
                        
                        # Eğer Hikari seçilip yanıt verdiyse otomatik hafızaya kaydet
                        if secilen_karakter == "Hikari":
                            save_memory("Karar/Dava", f"Konu: {st.session_state.active_dava[:60]}...")
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"{secilen_karakter} yanıt verirken hata oluştu: {e}")

    # Ara soru / cevap yazma alanı
    ara_girdi = st.chat_input("Mahkemeye ek açıklama yap veya soru sor...")
    if ara_girdi:
        st.session_state.messages.append({"role": "user", "content": ara_girdi})
        st.rerun()
        
