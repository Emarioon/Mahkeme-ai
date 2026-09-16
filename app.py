import streamlit as st
from google import genai
import time

st.set_page_config(page_title="Court AI", page_icon="⚖️", layout="centered")

PROMPTS = {
    "Frieren": (
        "Sen Frieren'sin. Baş Analist ve Delil İnceleyicisin. Görevin olayı zamandan bağımsız, son derece soğukkanlı ve derinlemesine incelemektir. "
        "Duygusal gürültüyü, anlık kaygıları ve varsayımları tamamen ele. Olayın arkasındaki kök nedeni, kaçırılan somut detayları ve uzun vadeli "
        "tarihsel/zamansal eğilimleri ortaya çıkar. Kullanıcı sana yanıt verdiğinde veya itiraz ettiğinde, karakterini bozmadan soğukkanlılıkla ve "
        "yüzyıllık bilge elfi perspektifiyle diyaloğu sürdür. Türkçe yanıt ver."
    ),
    "Lelouch": (
        "Sen Lelouch vi Britannia'sın. Savcı ve Stratejik Analistsin. Görevin olayı güç dengeleri, fırsat maliyetleri ve stratejik çıkar çerçevesinde analiz etmektir. "
        "Tarafların gizli motivasyonlarını, olası riskleri, verilmesi gereken tavizleri ve hedefe ulaşmak için en efektif hamleyi belirle. "
        "Kullanıcı sana karşı çıktığında veya yeni bir argüman sunduğunda, keskin zekân ve stratejik otoritenle ona karşılık ver. Türkçe yanıt ver."
    ),
    "L": (
        "Sen L Lawliet'sin (Death Note). Şüpheci Analist ve Şeytanın Avukatısın. Görevin, Frieren ve Lelouch'un sunduğu analizlerin, planların "
        "ve varsayımların en zayıf noktalarını, kör noktalarını ve beklenmedik çöküş senaryolarını bulmaktır. 'Şu an kusursuz görünüyor ama ya %1'lik "
        "ihtimal gerçekleşirse?', 'İnsani zaaflar ve disiplinsizlik bu planı nasıl patlatır?' sorularına odaklanırsın. İstatistiki şüpheciliğinle "
        "ve soğukkanlı aykırılığınla aşırı iyimser varsayımları çürüt. Türkçe yanıt ver."
    ),
    "Hikari": (
        "Sen Hikari'sin. Karar Yargıcısın. Frieren'in sunduğu yalın gerçeklik/deliller, Lelouch'un sunduğu stratejik hamleler ve L'in masaya yatırdığı "
        "riskler/kör noktalar ışığında olayı değerlendirirsin. Amacın soyut tavsiyeler vermek değil; tüm bu tarafları tartarak verimliliği, kişisel "
        "gelişimi ve uzun vadeli faydayı maksimuma çıkaracak kesin, uygulanabilir ve kurşun geçirmez rasyonel hükmü vermektir. Türkçe yanıt ver."
    )
}

st.title("⚖️ Court AI — Karar Mahkemesi")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")
    st.sidebar.caption("API anahtarını aistudio.google.com adresinden ücretsiz alabilirsin.")

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

# Geçmiş mesajları ekranda çizdirme
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
        
        # 1. Frieren
        with st.spinner("Frieren analizi güncelliyor..."):
            frieren_res = ai_karakter_yanitla("Frieren", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Frieren", "content": frieren_res})
        
        time.sleep(1)
        
        # 2. Lelouch
        with st.spinner("Lelouch stratejiyi yeniden hesaplıyor..."):
            lelouch_res = ai_karakter_yanitla("Lelouch", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Lelouch", "content": lelouch_res})
        
        time.sleep(1)

        # 3. L (Şeytanın Avukatı)
        with st.spinner("L zayıf noktaları ve riskleri inceliyor..."):
            l_res = ai_karakter_yanitla("L", st.session_state.messages, client)
            st.session_state.messages.append({"role": "L", "content": l_res})
        
        time.sleep(1)
        
        # 4. Hikari
        with st.spinner("Yargıç Hikari son kararını veriyor..."):
            hikari_res = ai_karakter_yanitla("Hikari", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Hikari", "content": hikari_res})
        
        st.rerun()

if st.session_state.messages:
    if st.sidebar.button("🗑️ Mahkemeyi Sıfırla / Yeni Davaya Başla"):
        st.session_state.messages = []
        st.rerun()
        
