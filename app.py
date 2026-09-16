import streamlit as st
from google import genai

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
    "Hikari": (
        "Sen Hikari'sin. Karar Yargıcısın. Frieren'in sunduğu yalın gerçeklik ve deliller ile Lelouch'un sunduğu stratejik risk ve fırsat analizlerini değerlendirirsin. "
        "Tartışma ilerledikçe, tarafların ve kullanıcının sunduğu yeni argümanlara göre nihai rasyonel kararı güncelle veya koru. Türkçe yanıt ver."
    )
}

st.title("⚖️ Court AI — Karar Mahkemesi")

# Secrets kontrolü
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")
    st.sidebar.caption("API anahtarını aistudio.google.com adresinden ücretsiz alabilirsin.")

# Oturum Hafızasını Başlatma
if "messages" not in st.session_state:
    st.session_state.messages = []

def ai_karakter_yanitla(rol_adi, sohbet_gecmisi, client):
    system_prompt = PROMPTS[rol_adi]
    
    # Tüm diyalog geçmişini karaktere bağlam olarak veriyoruz
    full_prompt = f"SYSTEM INSTRUCTION: {system_prompt}\n\n--- SOHBET GEÇMİŞİ VE MAHKEME SÜRECİ ---\n"
    for msg in sohbet_gecmisi:
        full_prompt += f"{msg['role']}: {msg['content']}\n"
    
    full_prompt += f"\nŞimdi {rol_adi} olarak bu diyaloga kendi perspektifinden yanıt ver:"
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"API Hatası: {e}"

# Ekrandaki Sohbet Geçmişini Çizdirme
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
    elif msg["role"] == "Hikari":
        st.subheader("⚖️ Hikari (Yargıç Kararı)")
        st.success(msg["content"])

# Yeni Mesaj / İkilem Giriş Alanı
yeni_girdi = st.chat_input("İkilemini yaz veya mahkemenin kararına yanıt ver...")

if yeni_girdi:
    if not api_key.strip():
        st.error("API Anahtarı bulunamadı!")
    else:
        client = genai.Client(api_key=api_key.strip())
        
        # 1. Kullanıcı mesajını ekle
        st.session_state.messages.append({"role": "Kullanıcı", "content": yeni_girdi})
        
        # 2. Frieren Yanıtı
        with st.spinner("Frieren analizi güncelliyor..."):
            frieren_res = ai_karakter_yanitla("Frieren", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Frieren", "content": frieren_res})
        
        # 3. Lelouch Yanıtı
        with st.spinner("Lelouch stratejiyi yeniden hesaplıyor..."):
            lelouch_res = ai_karakter_yanitla("Lelouch", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Lelouch", "content": lelouch_res})
        
        # 4. Hikari Yanıtı
        with st.spinner("Yargıç Hikari son kararını veriyor..."):
            hikari_res = ai_karakter_yanitla("Hikari", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Hikari", "content": hikari_res})
        
        # Ekranı tazeleyip yeni mesajları göster
        st.rerun()

# Oturumu Sıfırlama Butonu
if st.session_state.messages:
    if st.sidebar.button("🗑️ Mahkemeyi Sıfırla / Yeni Davaya Başla"):
        st.session_state.messages = []
        st.rerun()
            
