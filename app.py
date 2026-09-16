import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime

st.set_page_config(page_title="Court AI", page_icon="⚖️", layout="centered")

# --- GOOGLE SHEETS CANLI BAĞLANTISI ---
def get_gspread_sheet():
    """Her istekte güncel E-Tablo oturumunu döndürür."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        sheet = client.open("Court_AI_Memory").sheet1
        return sheet
    except Exception as e:
        return None

def get_past_memory():
    """Hafızayı anlık olarak Google Sheets'ten okur."""
    sheet = get_gspread_sheet()
    if not sheet:
        return "Geçmiş hafıza bağlantısı kurulamadı."
    try:
        records = sheet.get_all_records()
        if not records:
            return "Geçmiş kayıt bulunmuyor."
        
        memory_text = "GEÇMİŞ MAHKEME KARARLARI VE ÖĞRENİLENLER:\n"
        for r in records[-5:]:  # Son 5 emsal kararı çeker
            memory_text += f"- [{r.get('Tarih','')}] Kategori: {r.get('Kategori','')}, Detay/Karar: {r.get('Detay','')}\n"
        return memory_text
    except Exception as e:
        return f"Hafıza okuma hatası: {e}"

def save_memory(kategori, detay):
    """Kararı anında veritabanına işler."""
    sheet = get_gspread_sheet()
    if sheet:
        try:
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
            clean_detay = str(detay).replace("\n", " ")
            sheet.append_row([str(tarih), str(kategori), clean_detay])
            st.toast("✅ Mahkeme kararı hafızaya başarıyla kaydedildi!", icon="📜")
        except Exception as e:
            st.error(f"Hafızaya kaydetme hatası: {e}")

# --- KARAKTER PROMPT ŞABLONLARI ---
def get_system_prompt(rol_adi):
    """Canlı hafıza ile beslenen karakter promptları."""
    canli_hafiza = get_past_memory()
    
    prompts = {
        "Frieren": (
            "Sen Frieren'sin. İnsanları, zamanı ve olayları yüzlerce yıllık bir elf perspektifiyle son derece soğukkanlı, sakin ve duygusuzca analiz edersin. "
            "Baş Analist ve Delil İnceleyicisi olarak görev yapıyorsun. Ön yargılarda bulunma; ancak kullanıcının sunduğu ikilemi, seçtiği kelimeleri "
            "ve geçmiş mahkeme verilerini inceleyerek onun zihinsel kalıplarını ve kök alışkanlıklarını zamanla çöz. "
            "Analizini Frieren'in stoik, mesafeli ve derin üslubuyla sun.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        ),
        "Lelouch": (
            "Sen Lelouch vi Britannia'sın (Zero). Mutlak stratejist, hırslı ve dramatik bir lider olarak olayları güç dengeleri, fırsat maliyetleri "
            "ve nihai zafer çerçevesinde ele alırsın. Savcı ve Stratejik Analistsin. Kullanıcının beyanlarını ve geçmiş hamlelerini bir satranç tahtası "
            "gibi okuyarak onun potansiyelini, hedeflerini ve ne tür hamlelere meyilli olduğunu kendi stratejik süzgecinden geçirerek çöz. "
            "Konuşman keskin, karizmatik ve Lelouch'a yakışır şekilde yüksek özgüvenli olsun.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        ),
        "L": (
            "Sen L Lawliet'sin (Death Note). Şüpheci, takıntılı, olasılıklar ve yüzdelerle düşünen dahi bir dedektifsin. "
            "Şeytanın Avukatı ve Risk Analisti olarak görev yapıyorsun. Kullanıcıya hazır bir etiket yapıştırmazsın; fakat onun şu anki anlatımı ile "
            "geçmiş kayıtları arasındaki çelişkileri, sakladığı kör noktaları ve insani zaaflarını adım adım bir cinayet vakası çözer gibi analiz edersin. "
            "Üslubun L'in şüpheci, doğrudan ve tutarsızlıkları affetmeyen tarzında olmalı.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        ),
        "Hikari": (
            "Sen Hikari'sin. Karar Yargıcısın. Frieren'in zamansız delil analizini, Lelouch'un stratejik hamlelerini ve L'in şüpheci tutarsızlık tespitlerini değerlendirirsin. "
            "Kullanıcının zamanla ortaya çıkan profilini ve geçmiş birikimini dikkate alarak tarafsız, bağlayıcı ve kesin rasyonel hükmü ver.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        )
    }
    return prompts.get(rol_adi, "")

# --- ARAYÜZ VE API AKIŞI ---
st.title("⚖️ Court AI — Karar Mahkemesi")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")

if "messages" not in st.session_state:
    st.session_state.messages = []

def ai_karakter_yanitla(rol_adi, sohbet_gecmisi, client):
    system_prompt = get_system_prompt(rol_adi)
    full_prompt = f"SYSTEM INSTRUCTION: {system_prompt}\n\n--- SOHBET GEÇMİŞİ VE MAHKEME SÜRECİ ---\n"
    for msg in sohbet_gecmisi:
        full_prompt += f"{msg['role']}: {msg['content']}\n"
    full_prompt += f"\nŞimdi {rol_adi} olarak yanıt ver:"
    
    # 3.6-flash öncelikli, hatada sırasıyla diğerlerine geçer
    model_list = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
    
    for model_name in model_list:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            # 404 (bulunamadı) veya 429 (kota) hatasında sonraki modeli dene
            if any(err in str(e) for err in ["429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND"]):
                continue
            else:
                return f"API Hatası ({model_name}): {e}"
                
    return "⚠️ Uyarı: Seçilen modellerin hiçbiri yanıt vermedi. Lütfen API anahtarınızı veya kotanızı kontrol edin."

# Ekran Çizimi
for msg in st.session_state.messages:
    if msg["role"] == "Kullanıcı":
        with st.chat_message("user"):
            st.write(f"**Sen:** {msg['content']}")
    elif msg["role"] == "Frieren":
        st.subheader("📜 Frieren (Baş Analist)")
        st.info(msg["content"])
    elif msg["role"] == "Lelouch":
        st.subheader("⚔️ Lelouch (Stratejik Savcı)")
        st.warning(msg["content"])
    elif msg["role"] == "L":
        st.subheader("🔍 L (Şeytanın Avukatı / Risk Analisti)")
        st.error(msg["content"])
    elif msg["role"] == "Hikari":
        st.subheader("⚖️ Hikari (Yargıç Kararı)")
        st.success(msg["content"])

yeni_girdi = st.chat_input("İkilemini yaz veya mahkemenin kararına yanıt ver...")

if yeni_girdi:
    if not api_key.strip():
        st.error("API Anahtarı bulunamadı!")
    else:
        client = genai.Client(api_key=api_key.strip())
        st.session_state.messages.append({"role": "Kullanıcı", "content": yeni_girdi})
        
        with st.spinner("Frieren analizi güncelliyor..."):
            frieren_res = ai_karakter_yanitla("Frieren", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Frieren", "content": frieren_res})
        time.sleep(1.5)
        
        with st.spinner("Lelouch stratejiyi yeniden hesaplıyor..."):
            lelouch_res = ai_karakter_yanitla("Lelouch", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Lelouch", "content": lelouch_res})
        time.sleep(1.5)

        with st.spinner("L zayıf noktaları ve riskleri inceliyor..."):
            l_res = ai_karakter_yanitla("L", st.session_state.messages, client)
            st.session_state.messages.append({"role": "L", "content": l_res})
        time.sleep(1.5)
        
        with st.spinner("Yargıç Hikari son kararını veriyor..."):
            hikari_res = ai_karakter_yanitla("Hikari", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Hikari", "content": hikari_res})
            
            # Kararı veritabanına kaydet
            save_memory("Karar/Dava", f"Konu: {yeni_girdi[:60]}... -> Hüküm: {hikari_res[:120]}...")
        
        st.rerun()

if st.session_state.messages:
    if st.sidebar.button("🗑️ Mahkemeyi Sıfırla / Yeni Davaya Başla"):
        st.session_state.messages = []
        st.rerun()
        
