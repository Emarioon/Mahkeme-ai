import streamlit as st
import requests

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

def ai_karakter_yanitla(rol_adi, olay_metni, ekstra_baglam=""):
    system_prompt = PROMPTS[rol_adi]
    full_prompt = f"{system_prompt}\n\nOlay: {olay_metni}\n{ekstra_baglam}"
    
    # Standart Pollinations Text API uç noktası
    url = f"https://text.pollinations.ai/{requests.utils.quote(full_prompt)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # Bütçe hatasına düşmeyen doğrudan model yönlendirmesi
    params = {
        "model": "sur"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200 and response.text.strip():
            return response.text.strip()
        else:
            # Alternatif yedek motor çağrısı
            fallback_url = "https://text.pollinations.ai/"
            payload = {
                "messages": [{"role": "user", "content": full_prompt}],
                "model": "sur"
            }
            res_fallback = requests.post(fallback_url, json=payload, timeout=30)
            return res_fallback.text.strip()
    except Exception as e:
        return f"Bağlantı Hatası: {e}"

st.title("⚖️ Court AI — Karar Mahkemesi")
st.write("Karar vermekte zorlandığın olayı veya çatışmayı yaz, analiz başlasın.")

olay_input = st.text_area("Olay / İkilem", placeholder="Metni buraya yaz...", height=120)

if st.button("⚖️ Mahkemeyi Başlat", type="primary", use_container_width=True):
    if not olay_input.strip():
        st.warning("Lütfen bir olay yazın.")
    else:
        with st.spinner("Frieren derin delil analizini yapıyor..."):
            frieren_res = ai_karakter_yanitla("Frieren", olay_input)
        st.subheader("📜 Frieren (Baş Analist)")
        st.info(frieren_res)
        
        with st.spinner("Lelouch stratejik risk ve güç analizini hesaplıyor..."):
            lelouch_res = ai_karakter_yanitla("Lelouch", olay_input)
        st.subheader("⚔️ Lelouch (Stratejik Savcı)")
        st.warning(lelouch_res)
        
        baglam = f"Frieren Analizi: {frieren_res}\nLelouch Analizi: {lelouch_res}"
        with st.spinner("Hikari nihai rasyonel kararı veriyor..."):
            hikari_res = ai_karakter_yanitla("Hikari", olay_input, ekstra_baglam=baglam)
        st.subheader("⚖️ Hikari (Yargıç Kararı)")
        st.success(hikari_res)
        
