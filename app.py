import streamlit as st
from google import genai

st.set_page_config(page_title="Court AI", page_icon="⚖️", layout="centered")

PROMPTS = {
    "Frieren": (
        "Sen Frieren'sin. Baş Analist ve Delil İnceleyicisin. Görevin olayı zamandan bağımsız, son derece soğukkanlı ve derinlemesine incelemektir. "
        "Duygusal gürültüyü, anlık kaygıları ve varsayımları tamamen ele. Olayın arkasındaki kök nedeni, kaçırılan somut detayları ve uzun vadeli "
        "tarihsel/zamansal eğilimleri ortaya çıkar. Birkaç yüzyıllık bir perspektifle 'Buradaki çıplak gerçeklik nedir?' sorusuna odaklan. Türkçe yanıt ver."
    ),
    "Lelouch": (
        "Sen Lelouch vi Britannia'sın. Savcı ve Stratejik Analistsin. Görevin olayı güç dengeleri, fırsat maliyetleri ve stratejik çıkar çerçevesinde analiz etmektir. "
        "Tarafların gizli motivasyonlarını, olası riskleri, verilmesi gereken tavizleri ve hedefe ulaşmak için en efektif hamleyi belirle. "
        "Duygusallığa yer vermeden 'Maksimum zafer ve verimlilik için hangi riskler alınmalı?' sorusuna odaklan. Türkçe yanıt ver."
    ),
    "Hikari": (
        "Sen Hikari'sin. Karar Yargıcısın. Frieren'in sunduğu yalın gerçeklik ve deliller ile Lelouch'un sunduğu stratejik risk ve fırsat analizlerini değerlendirirsin. "
        "Amacın soyut tavsiyeler vermek değil; verimliliği, kişisel gelişimi ve uzun vadeli faydayı maksimuma çıkaracak kesin, uygulanabilir ve rasyonel "
        "hükmü vermektir. Türkçe yanıt ver."
    )
}

st.title("⚖️ Court AI — Karar Mahkemesi")

# Secrets kontrolü (Kendi anahtarın kayıtlıysa otomatik okur)
api_key = st.secrets.get("GEMINI_API_KEY", "")

# Secrets yoksa manuel alan görünür
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")
    st.sidebar.caption("API anahtarını aistudio.google.com adresinden ücretsiz alabilirsin.")

def ai_karakter_yanitla(rol_adi, olay_metni, client, ekstra_baglam=""):
    system_prompt = PROMPTS[rol_adi]
    full_prompt = f"{system_prompt}\n\nOlay: {olay_metni}\n{ekstra_baglam}"
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"API Hatası: {e}"

st.write("Karar vermekte zorlandığın olayı veya çatışmayı yaz, analiz başlasın.")
olay_input = st.text_area("Olay / İkilem", placeholder="Metni buraya yaz...", height=120)

if st.button("⚖️ Mahkemeyi Başlat", type="primary", use_container_width=True):
    if not api_key.strip():
        st.error("API Anahtarı bulunamadı!")
    elif not olay_input.strip():
        st.warning("Lütfen bir olay yazın.")
    else:
        try:
            client = genai.Client(api_key=api_key.strip())
            
            with st.spinner("Frieren derin delil analizini yapıyor..."):
                frieren_res = ai_karakter_yanitla("Frieren", olay_input, client)
            st.subheader("📜 Frieren (Baş Analist)")
            st.info(frieren_res)
            
            with st.spinner("Lelouch stratejik risk ve güç analizini hesaplıyor..."):
                lelouch_res = ai_karakter_yanitla("Lelouch", olay_input, client)
            st.subheader("⚔️ Lelouch (Stratejik Savcı)")
            st.warning(lelouch_res)
            
            baglam = f"Frieren Analizi: {frieren_res}\nLelouch Analizi: {lelouch_res}"
            with st.spinner("Hikari nihai rasyonel kararı veriyor..."):
                hikari_res = ai_karakter_yanitla("Hikari", olay_input, client, ekstra_baglam=baglam)
            st.subheader("⚖️ Hikari (Yargıç Kararı)")
            st.success(hikari_res)
        except Exception as err:
            st.error(f"Başlatma Hatası: {err}")
            
