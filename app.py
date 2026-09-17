import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime

# --- SAYFA AYARLARI & GÖZ YORMAYAN MAT MAHKEME TEMASI (CSS) ---
st.set_page_config(page_title="Court AI — Karar Mahkemesi", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
    /* Mahkeme Kartları - Dark Tema */
    .char-card {
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 18px;
        border-left: 6px solid;
        line-height: 1.6;
        font-size: 0.98em;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .frieren-card { background-color: #1e2630; border-color: #64b5f6; color: #e3f2fd; }
    .lelouch-card { background-color: #2a1824; border-color: #ec407a; color: #fce4ec; }
    .l-card { background-color: #212121; border-color: #b0bec5; color: #eceff1; }
    .yagmur-card { background-color: #261c33; border-color: #ab47bc; color: #f3e5f5; }
    .hikari-card { background-color: #2d2615; border-color: #ffee58; color: #fffde7; }
    
    .char-header {
        font-weight: 700;
        font-size: 1.1em;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        letter-spacing: 0.5px;
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
            "Mizaç olarak son derece zeki, stratejik, doğrudan ve hızlısın. Lafı dolandırmayı, soyut/genel geçer tavsiyeler vermeyi hiç sevmezsin. Bir problem gördüğünde 'Ne yapıyoruz, adım ne?' diyerek olayı doğrudan operasyonel bir karara bağlarsın. "
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

# SIDEBAR
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

# API ÇAĞRI FONKSİYONU (Sınırsız Token & Kesin Türkçe Zorlaması)
def ai_karakter_yanitla(rol_adi, sohbet_gecmisi, client):
    system_prompt = get_system_prompt(rol_adi)
    
    full_prompt = (
        f"ÖNEMLİ KURAL: Yanıtının tamamını KESİNLİKLE Türkçe olarak yazacaksın. "
        f"Araya tek bir İngilizce kelime veya cümle karıştırma.\n\n"
        f"SYSTEM INSTRUCTION: {system_prompt}\n\n"
        f"--- SOHBET GEÇMİŞİ VE MAHKEME SÜRECİ ---\n"
    )
    for msg in sohbet_gecmisi:
        full_prompt += f"{msg['role']}: {msg['content']}\n"
    
    full_prompt += f"\nŞimdi {rol_adi} olarak eksiksiz, detaylı ve tamamen Türkçe yanıt ver:"
    
    # Doğrudan Gemini 3.6 Flash modeli tanımlandı
    target_model = 'gemini-3.6-flash'
    
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=full_prompt,
                config={
                    "temperature": 0.7
                }
            )
            if response and hasattr(response, 'text') and response.text:
                return response.text.strip()
            else:
                raise Exception("Boş yanıt döndü")
        except Exception as e:
            if attempt == 0:
                time.sleep(3.0)
                continue
            return f"⚠️ {rol_adi} yanıt verirken sunucu yoğunluğuna takıldı."

# Duruşma Geçmişi
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

# GİRDİ VE AKIŞ ALANI
yeni_girdi = st.chat_input("İkilemini yaz veya mahkemenin sorularına yanıt ver...")

if yeni_girdi:
    if not api_key.strip():
        st.error("API Anahtarı bulunamadı!")
    else:
        client = genai.Client(api_key=api_key.strip())
        st.session_state.messages.append({"role": "Kullanıcı", "content": yeni_girdi})
        
        karakterler = ["Frieren", "Lelouch", "L", "Yağmur", "Hikari"]
        
        for k in karakterler:
            with st.spinner(f"⏳ {k} değerlendiriyor..."):
                res = ai_karakter_yanitla(k, st.session_state.messages, client)
                st.session_state.messages.append({"role": k, "content": res})
            time.sleep(1.5)
            
        save_memory("Karar/Dava", f"Konu: {yeni_girdi[:60]}...")
        st.rerun()
    
