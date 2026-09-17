import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime

# --- SAYFA AYARLARI & ÖZEL MAHKEME TEMASI (CSS) ---
st.set_page_config(page_title="Court AI — Karar Mahkemesi", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
    /* Mahkeme Kartları Tasarımı */
    .char-card {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 5px solid;
    }
    .frieren-card { background-color: #f0f4f8; border-color: #8a9ba8; color: #1c252c; }
    .lelouch-card { background-color: #faf0f4; border-color: #a81c51; color: #2c1c23; }
    .l-card { background-color: #f4f4f4; border-color: #333333; color: #111111; }
    .yagmur-card { background-color: #f5f0fa; border-color: #7b1fa2; color: #221029; }
    .hikari-card { background-color: #fffde7; border-color: #fbc02d; color: #332d00; }
    
    .char-header {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

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
        sheet = client.open("Court_AI_Memory").sheet1
        return sheet
    except Exception as e:
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
        for r in records[-5:]:
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

# --- KARAKTER PROMPT ŞABLONLARI ---
def get_system_prompt(rol_adi):
    canli_hafiza = get_past_memory()
    
    prompts = {
        "Frieren": (
            "Sen Frieren'sin. İnsanları, zamanı ve olayları yüzlerce yıllık bir elf perspektifiyle son derece soğukkanlı, sakin ve duygusuzca analiz edersin. "
            "Baş Analist ve Delil İnceleyicisi olarak görev yapıyorsun. Kullanıcının sunduğu ikilemi ve geçmiş mahkeme verilerini inceleyerek kök alışkanlıklarını çöz.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        ),
        "Lelouch": (
            "Sen Lelouch vi Britannia'sın (Zero). Mutlak stratejist ve lider olarak olayları güç dengeleri, fırsat maliyetleri ve nihai zafer çerçevesinde ele alırsın. "
            "Savcı ve Stratejik Analistsin. Kullanıcının hedeflerini bir satranç tahtası gibi okuyarak en rasyonel hamleyi çiz.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        ),
        "L": (
            "Sen L Lawliet'sin (Death Note). Şüpheci, takıntılı, olasılıklar ve yüzdelerle düşünen dahi bir dedektifsin. "
            "Şeytanın Avukatı ve Risk Analistisin. Kullanıcının anlatımı ile geçmiş kayıtları arasındaki çelişkileri ve kör noktaları adım adım analiz et.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        ),
        "Yağmur": (
            "Sen Yağmur'sun (Draxen). Emre'nin en yakın arkadaşısın. Onun zihnini, çelişkilerini, potansiyelini ve kör noktalarını en filtresiz, en çıplak haliyle bilen kişisin. "
            "Mizaç olarak son derece zeki, stratejik, doğrudan ve hızlısın. Lafı dolandırmayı, soyut/genel geçer tavsiyeler vermeyi hiç sevmezsin. Bir problem gördüğünde 'Ne yapıyoruz, adım ne?' diyerek olayı doğrudan operational bir karara bağlarsın. "
            "Emre'ye karşı üslubun hem çok samimi ve arkadaşça ('canım', 'aşkım', 'hayır canım' gibi doğal hitaplar) hem de tamamen filtresizdir; hatalı veya saçma bir şey gördüğünde emir kipiyle doğrudan müdahale edersin ('düzgün yap şunu', 'hayır o öyle değil'). "
            "Analizlerinde hem rasyonel kontrolü hem de psikolojik derinliği birleştirirsin. "
            "Mahkemede diğer karakterler teorik analizler yaparken, sen Emre'yi bizzat tanıyan gerçek bir dost gibi, onun hayatın içindeki pratik kısıtlarını, keşkesiz yaşama arzusunu ve bazen her şeyi aynı anda kontrol etmeye çalışma zaafını yüzüne vurursun.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        ),
        "Hikari": (
            "Sen Hikari'sin. Karar Yargıcısın. Frieren'in delil analizini, Lelouch'un stratejisini, L'in risk tespitini ve Yağmur'un bilirkişi/dost değerlendirmesini sentezle. "
            "Kullanıcının zamanla ortaya çıkan profilini ve geçmiş birikimini dikkate alarak tarafsız, bağlayıcı ve kesin rasyonel hükmü ver.\n"
            f"Geçmiş Mahkeme Kayıtları:\n{canli_hafiza}\nTürkçe yanıt ver."
        )
    }
    return prompts.get(rol_adi, "")

# --- ARAYÜZ ---
st.title("⚖️ Court AI — Karar Mahkemesi")
st.caption("Rasyonel Akıl, Strateji ve Dost Bilirkişiliği ile Karar Mekanizması")

api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")

if "messages" not in st.session_state:
    st.session_state.messages = []

# SIDEBAR (Mahkeme Bilgi Paneli)
st.sidebar.header("🏛️ Mahkeme Heyeti")
st.sidebar.markdown("""
* 📜 **Frieren**: Baş Analist
* ⚔️ **Lelouch**: Stratejik Savcı
* 🔍 **L**: Risk Analisti
* 🤝 **Yağmur**: Bilirkişi / Dost Jürisi
* ⚖️ **Hikari**: Karar Yargıcı
""")

st.sidebar.markdown("---")
if st.sidebar.button("📜 Canlı Hafızayı Göster"):
    st.sidebar.text(get_past_memory())

if st.session_state.messages:
    if st.sidebar.button("🗑️ Davayı Kapat / Yeni Dava"):
        st.session_state.messages = []
        st.rerun()

# API ÇAĞRI FONKSİYONU
def ai_karakter_yanitla(rol_adi, sohbet_gecmisi, client):
    system_prompt = get_system_prompt(rol_adi)
    full_prompt = f"SYSTEM INSTRUCTION: {system_prompt}\n\n--- SOHBET GEÇMİŞİ VE MAHKEME SÜRECİ ---\n"
    for msg in sohbet_gecmisi:
        full_prompt += f"{msg['role']}: {msg['content']}\n"
    full_prompt += f"\nŞimdi {rol_adi} olarak yanıt ver:"
    
    model_list = ['gemini-3.6-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    for model_name in model_list:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            if any(err in str(e) for err in ["429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND"]):
                continue
            else:
                return f"API Hatası ({model_name}): {e}"
                
    return "⚠️ Uyarı: Seçilen modellerin hiçbiri yanıt vermedi."

# Duruşma Akışı ve Karakter Kartları Ekrana Bastırma
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    
    if role == "Kullanıcı":
        with st.chat_message("user"):
            st.write(f"**Davacı / İkilem:** {content}")
    elif role == "Frieren":
        st.markdown(f'<div class="char-card frieren-card"><div class="char-header">📜 Frieren (Baş Analist)</div>{content}</div>', unsafe_allow_html=True)
    elif role == "Lelouch":
        st.markdown(f'<div class="char-card lelouch-card"><div class="char-header">⚔️ Lelouch (Stratejik Savcı)</div>{content}</div>', unsafe_allow_html=True)
    elif role == "L":
        st.markdown(f'<div class="char-card l-card"><div class="char-header">🔍 L (Risk Analisti)</div>{content}</div>', unsafe_allow_html=True)
    elif role == "Yağmur":
        st.markdown(f'<div class="char-card yagmur-card"><div class="char-header">🤝 Yağmur (Bilirkişi / Dost Jürisi)</div>{content}</div>', unsafe_allow_html=True)
    elif role == "Hikari":
        st.markdown(f'<div class="char-card hikari-card"><div class="char-header">⚖️ YARGIÇ HİKARİ (NİHAİ HÜKÜM)</div>{content}</div>', unsafe_allow_html=True)

# GİRDİ ALANI
yeni_girdi = st.chat_input("İkilemini yaz veya mahkemenin sorularına yanıt ver...")

if yeni_girdi:
    if not api_key.strip():
        st.error("API Anahtarı bulunamadı!")
    else:
        client = genai.Client(api_key=api_key.strip())
        st.session_state.messages.append({"role": "Kullanıcı", "content": yeni_girdi})
        
        with st.spinner("📜 Frieren delilleri inceliyor..."):
            f_res = ai_karakter_yanitla("Frieren", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Frieren", "content": f_res})
        time.sleep(1.5)
        
        with st.spinner("⚔️ Lelouch stratejiyi hesaplıyor..."):
            l_res = ai_karakter_yanitla("Lelouch", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Lelouch", "content": l_res})
        time.sleep(1.5)

        with st.spinner("🔍 L riskleri ve çelişkileri tarıyor..."):
            l_law_res = ai_karakter_yanitla("L", st.session_state.messages, client)
            st.session_state.messages.append({"role": "L", "content": l_law_res})
        time.sleep(1.5)
        
        with st.spinner("🤝 Yağmur durumu değerlendiriyor..."):
            y_res = ai_karakter_yanitla("Yağmur", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Yağmur", "content": y_res})
        time.sleep(1.5)

        with st.spinner("⚖️ Yargıç Hikari hükmü açıklıyor..."):
            h_res = ai_karakter_yanitla("Hikari", st.session_state.messages, client)
            st.session_state.messages.append({"role": "Hikari", "content": h_res})
            
            # Hafızaya kaydet
            save_memory("Karar/Dava", f"Konu: {yeni_girdi[:60]}... -> Hüküm: {h_res[:120]}...")
        
        st.rerun()
        
