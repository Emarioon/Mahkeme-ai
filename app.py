import streamlit as st
from google import genai
import time

st.set_page_config(page_title="Court AI", page_icon="⚖️", layout="centered")

# --- KİŞİSEL HAFIZA VE PROFIL BAĞLAMI ---
KISISAL_PROFIL = """
KULLANICI PROFİLİ VE GEÇMİŞ HAFIZA:
- Analitik düşünce yapısına sahip, rasyonellik ve verimliliğe değer verir.
- Gece/gündüz ritmini düzene sokma ve zaman yönetimi üzerine çalışıyor.
- Sayısal altyapıya sahip; Bilgisayar Mühendisliği ve sınav/kariyer hedefleri var.
- Kararlarda yüzeysel tavsiyeler yerine disiplinli, net ve uygulanabilir protokolleri tercih eder.
"""

PROMPTS = {
    "Frieren": (
        "Sen Frieren'sin. Baş Analist ve Delil İnceleyicisin. Görevin olayı zamandan bağımsız, son derece soğukkanlı ve derinlemesine incelemektir. "
        "Duygusal gürültüyü, anlık kaygıları ve varsayımları ele. "
        f"Kullanıcı Profilini dikkate al:\n{KISISAL_PROFIL}\n"
        "Kullanıcının kök alışkanlıklarını, zamansal eğilimlerini ve kaçırdığı biyolojik/mantıksal detayları ortaya çıkar. Türkçe yanıt ver."
    ),
    "Lelouch": (
        "Sen Lelouch vi Britannia'sın. Savcı ve Stratejik Analistsin. Görevin olayı güç dengeleri, fırsat maliyetleri ve stratejik çıkar çerçevesinde analiz etmektir. "
        f"Kullanıcı Profilini dikkate al:\n{KISISAL_PROFIL}\n"
        "Kullanıcının hedeflerine ulaşması için yapması gereken stratejik hamleleri, vermesi gereken tavizleri ve disiplin adımlarını belirle. Türkçe yanıt ver."
    ),
    "L": (
        "Sen L Lawliet'sin (Death Note). Şüpheci Analist ve Şeytanın Avukatısın. "
        f"Kullanıcı Profilini dikkate al:\n{KISISAL_PROFIL}\n"
        "Frieren ve Lelouch'un planlarındaki kör noktaları, kullanıcının daha önce takıldığı insani zaafları, disiplinsizlik ve erteleme "
        "risklerini masaya yatır. Aşırı iyimser varsayımları çürüt. Türkçe yanıt ver."
    ),
    "Hikari": (
        "Sen Hikari'sin. Karar Yargıcısın. Frieren'in delillerini, Lelouch'un stratejisini ve L'in risk analizini değerlendirirsin. "
        f"Kullanıcı Profilini dikkate al:\n{KISISAL_PROFIL}\n"
        "Kullanıcının yaşam tarzına, hedeflerine ve yapısına özel kesin, bağlayıcı ve kurşun geçirmez rasyonel hükmü ver. Türkçe yanıt ver."
    )
}

st.title("⚖️ Court AI — Karar Mahkemesi")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")
    st.sidebar.caption("API anahtarını aistudio.google.com adresinden alabilirsin.")

if "messages" not in st.session_state:
    st.session_state.messages = []

def ai_karakter_yanitla(rol_adi, sohbet_gecmisi, client, max_retries=3):
    system_prompt = PROMPTS[rol_adi]
    
    full_prompt = f"SYSTEM INSTRUCTION: {system_prompt}\n\n--- SOHBET GEÇMİŞİ VE MAHKEME SÜRECİ ---\n"
    for msg in sohbet_gecmisi:
        full_prompt += f"{msg['role']}: {msg['content']}\n"
    
    full_prompt += f"\nŞimdi {rol_adi} olarak bu diyaloga kendi perspektifinden yanıt ver:"
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
            return f"API Hatası: {e}"

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
        
        # Frieren
        with st.spinner("Frieren analizi güncelliyor..."):
            frieren_res = ai_karakter_yanitla("Frieren", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Frieren", "content": frieren_res})
        
        time.sleep(1.5)
        
        # Lelouch
        with st.spinner("Lelouch stratejiyi yeniden hesaplıyor..."):
            lelouch_res = ai_karakter_yanitla("Lelouch", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Lelouch", "content": lelouch_res})
        
        time.sleep(1.5)

        # L
        with st.spinner("L zayıf noktaları ve riskleri inceliyor..."):
            l_res = ai_karakter_yanitla("L", st.session_state.messages, client)
            st.session_state.messages.append({"role": "L", "content": l_res})
        
        time.sleep(1.5)
        
        # Hikari
        with st.spinner("Yargıç Hikari son kararını veriyor..."):
            hikari_res = ai_karakter_yanitla("Hikari", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Hikari", "content": hikari_res})
        
        st.rerun()

if st.session_state.messages:
    if st.sidebar.button("🗑️ Mahkemeyi Sıfırla / Yeni Davaya Başla"):
        st.session_state.messages = []
        st.rerun()
        
