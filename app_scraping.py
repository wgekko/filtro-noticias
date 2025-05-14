import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json

OLLAMA = "http://localhost:11434"
MODEL = "gemma3:1b"

# URLs de las páginas de economía
URLS = {
    "Infobae": "https://www.infobae.com/economia/",
    "Ambito": "https://www.ambito.com/economia",
    "Cronista": "https://www.cronista.com/ultimas-noticias/"
}

def ollama_tldr(text: str) -> str:
    r = requests.post(f"{OLLAMA}/api/generate",
                      json={"model": MODEL,
                            "prompt": f"Give a one sentence summary of the following news content, and only print that one sentence:\n{text}",
                            "temperature": 0.3,
                            "stream": False},
                      timeout=120)
    r.raise_for_status()
    return r.json()["response"].strip()

def fetch_news(url: str, max_n: int) -> list:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Dependiendo del sitio, los selectores pueden variar
    if "infobae" in url:
        items = soup.select('.article-title a')[:max_n]
    elif "ambito" in url:
        items = soup.select('.title a')[:max_n]
    elif "cronista" in url:
        items = soup.select('.title a')[:max_n]
    else:
        return []

    news = []
    for item in items:
        title = item.get_text(strip=True)
        link = item['href']
        summary = ""  # Algunos sitios no proporcionan un resumen directo
        news.append({"title": title, "link": link, "summary": summary})
    return news

@st.cache_data(ttl=3600)
def fetch_papers(sources, max_n):
    rows = []
    for source in sources:
        url = URLS.get(source)
        if url:
            news_items = fetch_news(url, max_n)
            for news in news_items:
                summary = news["summary"] or "No summary available"
                tldr = ollama_tldr(summary)
                rows.append({
                    "source": source,
                    "title": news["title"],
                    "link": news["link"],
                    "tldr": tldr
                })
                time.sleep(0.1)  # Polite to Ollama
    return pd.DataFrame(rows)

st.sidebar.title("Radar de Economía (Ollama)")
sel = st.sidebar.multiselect("Fuentes", list(URLS.keys()), ["Infobae", "Ambito", "Cronista"])
max_n = st.sidebar.slider("Noticias por fuente", 5, 30, 10)
if st.sidebar.button("Actualizar ahora"):
    st.cache_data.clear()

df = fetch_papers(sel, max_n)
query = st.text_input("Filtrar por palabra clave")
if query:
    df = df[df["tldr"].str.contains(query, case=False) | df["title"].str.contains(query, case=False)]

st.dataframe(df)
csv = df.to_csv(index=False, encoding="utf-8-sig")
st.download_button("⬇️ Descargar CSV", csv, "noticias_economia.csv")

st.caption("Resúmenes locales con Gemma 3 1B en Ollama — sin llaves en la nube ")



# --------------- footer -----------------------------
st.write("---")
with st.container():
  #st.write("---")
  st.write("&copy; - derechos reservados -  2025 -  Walter Gómez - FullStack Developer - Data Science - Business Intelligence")
  #st.write("##")
  left, right = st.columns(2, gap='medium', vertical_alignment="bottom")
  with left:
    #st.write('##')
    st.link_button("Mi LinkedIn", "https://www.linkedin.com/in/walter-gomez-fullstack-developer-datascience-businessintelligence-finanzas-python/",use_container_width=True)
  with right: 
     #st.write('##') 
    st.link_button("Mi Porfolio", "https://walter-portfolio-animado.netlify.app/", use_container_width=True)
      