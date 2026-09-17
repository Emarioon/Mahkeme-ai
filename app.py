import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Court AI — Karar Mahkemesi", page_icon="⚖️", layout="centered")

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

# --- TEK İSTEKLİ MAHKEME PANELİ PROMPTU ---
def build_court_prompt(user_input, sohbet_gecmisi):
    canli_hafiza = get_past_memory()
    
    kisa_gecmis = sohbet_gecmisi[-4:] if len(sohbet_gecmisi) > 4 else sohbet_gecmisi
    gecmis_metni = ""
    for msg in kisa_gecmis:
        gecmis_metni += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
ÖNEMLİ KURAL: Bütün karakterlerin yanıtları KESİNLİKLE Türkçe olacaktır. Araya İngilizce kelime karıştırma.

Sen bir Mahkeme Heyeti Simülatörüsün. Aşağıda tanımlanan 5 farklı karakter sırayla kendi benzersiz kimlikleri ve üsluplarıyla kullanıcının sunduğu ikilemi değerlendirecektir.

--- GEÇMİŞ MAHKEME EMSAL KAYITLARI ---
{canli_hafiza}

--- SOHBET GEÇMİŞİ ---
{gecmis_metni}

--- MEVCUT DURUŞMA İKİLEMİ ---
Kullanıcı: {user_input}

--- KARAKTER ROLLERİ VE TALİMATLAR ---
1. **Frieren (Baş Analist & Delil İnceleyici)**:
   - Yüzlerce yıllık elf soğukkanlılığıyla son derece sakin, mantıksal ve duygusuzca yaklaş.
   - Kullanıcının ikilemini ve geçmiş verilerini inceleyerek kök alışkanlıklarını çöz.

2. **Lelouch (Stratejik Savcı & Zero)**:
   - Mutlak stratejist olarak güç dengeleri, fırsat maliyetleri ve nihai zafer çerçevesinde konuş.
   - Kullanıcının hedeflerini bir satranç tahtası gibi okuyarak en rasyonel hamleyi çiz.

3. **L (Risk Analisti & Şeytanın Avukatı)**:
   - Şüpheci, olasılıklar ve yüzdelerle düşünen dahi dedektif üslubu kullan.
   - Anlatımdaki çelişkileri, kör noktaları ve riskleri adım adım çıkar.

4. **Yağmur (Bilirkişi / Dost Jürisi - Draxen)**:
   - Emre'nin en yakın arkadaşısın. Onun zihnini, çelişkilerini ve potansiyelini en filtresiz bilen kişisin.
   - Zeki, stratejik, doğrudan ve operasyonel konuş. Lafı dolandırma ('Ne yapıyoruz, adım ne?').
   - Üslubun samimi ('canım', 'hayır canım') ama filtresiz ve yapıcı bir şekilde sert olsun.

5. **Hikari (Karar Yargıcı)**:
   - Frieren, Lelouch, L ve Yağmur'un değerlendirmelerini sentezle.
   - Kullanıcının geçmiş birikimini dikkate alarak tarafsız, bağlayıcı ve kesin rasyonel nihai hükmü ver.

--- ÇIKTI FORMATI ---
Yanıtını TAM OLARAK aşağıdaki başlık düzeninde ver:

### 📜 Frieren (Baş Analist)
[Frieren'in analizi]

### ⚔️ Lelouch (Stratejik Savcı)
[Lelouch'un stratejisi]

### 🔍 L (Risk Analisti)
[L'in risk değerlendirmesi]

### 🤝 Yağmur (Bilirkişi / Dost Jürisi)
[Yağmur'un değerlendirmesi]

### ⚖️ YARGIÇ HİKARİ (NİHAİ HÜKÜM)
[Hikari'nin nihai kararı]
"""
    return prompt

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

# DURUŞMA GEÇMİŞİ EKRANI
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# GİRDİ VE AKIŞ ALANI
yeni_girdi = st.chat_input("İkilemini yaz veya mahkemenin sorularına yanıt ver...")

if yeni_girdi:
    if not api_key.strip():
        st.error("API Anahtarı bulunamadı!")
    else:
        client = genai.Client(api_key=api_key.strip())
        
        st.session_state.messages.append({"role": "user", "content": yeni_girdi})
        with st.chat_message("user"):
            st.markdown(yeni_girdi)

        with st.spinner("⚖️ Mahkeme heyeti davayı değerlendiriyor..."):
            try:
                full_prompt = build_court_prompt(yeni_girdi, st.session_state.messages)
                
                # Sadece gemini-3.6-flash kullanılıyor
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=full_prompt,
                    config={"temperature": 0.7}
                )
                
                mahkeme_karari = response.text.strip()
                
                st.session_state.messages.append({"role": "assistant", "content": mahkeme_karari})
                with st.chat_message("assistant"):
                    st.markdown(mahkeme_karari)
                
                save_memory("Karar/Dava", f"Konu: {yeni_girdi[:60]}...")
                
            except Exception as e:
                st.error(f"Mahkeme değerlendirmesi sırasında bir hata oluştu: {e}")
                
