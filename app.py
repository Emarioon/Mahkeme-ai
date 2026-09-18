import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Court AI — Adım Adım Duruşma", page_icon="⚖️", layout="centered")

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

# --- TEK TEK KARAKTER PROMPT OLUŞTURUCU ---
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
st.title("⚖️ Court AI — Adım Adım Duruşma")
st.caption("Sıralı Mahkeme Akışı")

api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")

# SESSION STATE TANIMLARI
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_step" not in st.session_state:
    st.session_state.current_step = 0  # 0: Bekliyor, 1: Frieren, 2: Lelouch, 3: L, 4: Yağmur, 5: Hikari
if "active_dava" not in st.session_state:
    st.session_state.active_dava = ""

KARAKTER_LISTESI = ["Frieren", "Lelouch", "L", "Yağmur", "Hikari"]

# SIDEBAR
st.sidebar.header("🏛️ Mahkeme Heyeti")
st.sidebar.markdown("""
1. 📜 **Frieren**: Baş Analist
2. ⚔️ **Lelouch**: Stratejik Savcı
3. 🔍 **L**: Risk Analisti
4. 🤝 **Yağmur**: Bilirkişi / Dost Jürisi
5. ⚖️ **Hikari**: Karar Yargıcı
""")

st.sidebar.markdown("---")
if st.sidebar.button("📜 Canlı Hafızayı Göster"):
    st.sidebar.text(get_past_memory())

if st.sidebar.button("🗑️ Davayı Kapat / Yeni Dava"):
    st.session_state.messages = []
    st.session_state.current_step = 0
    st.session_state.active_dava = ""
    st.rerun()

# GEÇMİŞ MESAJLARI EKRANA YAZDIR
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# YENİ DAVA BAŞLATMA ALANI
if st.session_state.current_step == 0:
    yeni_girdi = st.chat_input("İkilemini yazarak duruşmayı başlat...")
    if yeni_girdi:
        if not api_key.strip():
            st.error("API Anahtarı bulunamadı!")
        else:
            st.session_state.active_dava = yeni_girdi
            st.session_state.messages.append({"role": "user", "content": yeni_girdi})
            st.session_state.current_step = 1  # Frieren'e geç
            st.rerun()

# ADIM ADIM İLERLEME MEKANİZMASI
if 1 <= st.session_state.current_step <= 5:
    current_char = KARAKTER_LISTESI[st.session_state.current_step - 1]
    
    # Eğer bu karakter henüz yanıt vermediyse buton göster
    button_label = f"🎙️ {current_char} Söz Alsın"
    
    if st.button(button_label, type="primary"):
        client = genai.Client(api_key=api_key.strip())
        
        with st.spinner(f"⚖️ {current_char} değerlendirmesini yapıyor..."):
            try:
                prompt = get_single_character_prompt(current_char, st.session_state.active_dava, st.session_state.messages)
                
                # Sadece gemini-3.6-flash
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt,
                    config={"temperature": 0.7}
                )
                
                res_text = response.text.strip()
                formatted_res = f"### {current_char}\n{res_text}"
                
                st.session_state.messages.append({"role": current_char, "content": formatted_res})
                
                # Hikari yanıt verdiyse davayı kapat ve hafızaya kaydet
                if current_char == "Hikari":
                    save_memory("Karar/Dava", f"Konu: {st.session_state.active_dava[:60]}...")
                    st.session_state.current_step = 6 # Duruşma bitti
                else:
                    st.session_state.current_step += 1 # Sonraki karaktere geç
                
                st.rerun()
                
            except Exception as e:
                st.error(f"{current_char} yanıt verirken hata oluştu: {e}")

if st.session_state.current_step == 6:
    st.success("🏛️ Duruşma tamamlandı ve karar hafızaya kaydedildi.")
    
