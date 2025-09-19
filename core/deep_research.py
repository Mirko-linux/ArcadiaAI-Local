import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from typing import List, Dict

# --- CONFIG ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
]
SEARCH_ENGINES = {
    "duckduckgo": {
        "url": "https://html.duckduckgo.com/html/",
        "method": "POST",
        "params": {"q": "", "kl": "it-it"}
    },
    "brave": {
        "url": "https://search.brave.com/search",
        "method": "GET",
        "params": {"q": ""}
    }
}

class ContentAnalyzer:
    def calculate_relevance(self, query: str, text: str, url: str) -> float:
        score = 0
        q_words = query.lower().split()
        text_lower = text.lower()
        for word in q_words:
            if word in text_lower:
                score += 1
        return min(score / len(q_words), 1.0)

    def extract_entities(self, text: str) -> List[str]:
        # Estrai date, email, URL, ecc.
        dates = re.findall(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b', text)
        emails = re.findall(r'\S+@\S+\.\S+', text)
        return list(set(dates + emails))[:5]

async def search_duckduckgo(query: str) -> List[Dict]:
    async with aiohttp.ClientSession() as session:
        engine = SEARCH_ENGINES["duckduckgo"]
        async with session.post(engine["url"], data=engine["params"]) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            for h in soup.find_all('a', href=True):
                href = h['href']
                if href.startswith('https://') and not 'duckduckgo' in href:
                    title = h.get_text(strip=True)
                    results.append({"title": title, "url": href})
                    if len(results) >= 3:
                        break
            return results

async def search_brave(query: str) -> List[Dict]:
    async with aiohttp.ClientSession() as session:
        engine = SEARCH_ENGINES["brave"]
        params = {**engine["params"], "q": query}
        async with session.get(engine["url"], params=params) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            for a in soup.select('main a'):
                href = a.get('href')
                if href and href.startswith('http'):
                    title = a.get_text(strip=True)
                    results.append({"title": title, "url": href})
                    if len(results) >= 3:
                        break
            return results

async def deep_research(query: str) -> Dict:
    """Esegue una ricerca approfondita usando motori etici"""
    analyzer = ContentAnalyzer()
    try:
        # Ricerca su più motori
        ddg_results = await search_duckduckgo(query)
        brave_results = await search_brave(query)
        all_results = ddg_results + brave_results

        # Deduplica per dominio
        seen_domains = set()
        unique_results = []
        for res in all_results:
            domain = urlparse(res["url"]).netloc
            if domain not in seen_domains:
                unique_results.append(res)
                seen_domains.add(domain)

        # Scarica e analizza i primi 3 risultati
        final_results = []
        for res in unique_results[:3]:
            try:
                response = requests.get(res["url"], timeout=10, headers={"User-Agent": USER_AGENTS[0]})
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()[:2000]  # Primi 2000 caratteri
                relevance = analyzer.calculate_relevance(query, text, res["url"])
                entities = analyzer.extract_entities(text)
                final_results.append({
                    "title": res["title"],
                    "url": res["url"],
                    "text": text,
                    "relevance": relevance,
                    "entities": entities
                })
            except:
                continue

        return {
            "query": query,
            "results": final_results,
            "count": len(final_results)
        }
    except Exception as e:
        return {"error": str(e), "results": []}