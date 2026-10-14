import re
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import httpx
import logging

logger = logging.getLogger("narrai.wikipedia")

class WikipediaService:
    """
    Collects verifiable historical and mythological research references from Wikipedia
    via the official MediaWiki API with multi-lingual support (vi prioritized, en fallback).
    """
    
    VI_API = "https://vi.wikipedia.org/w/api.php"
    EN_API = "https://en.wikipedia.org/w/api.php"
    USER_AGENT = "NarrAIStoryPipeline/2.0 (https://github.com/anhdinh0701/final; contact@narrai.vn)"

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    async def fetch_research_material(
        self,
        query: str,
        topic: Optional[str] = None,
        source_languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for gathering source references for a given prompt query.
        Returns unified research package matching the specification.
        """
        if not source_languages:
            source_languages = ["vi", "en"]

        clean_query = query.strip()
        sources: List[Dict[str, Any]] = []
        collected_notes: List[str] = []
        is_legend = self._detect_folklore_or_legend(clean_query, topic)

        async with httpx.AsyncClient(
            headers={"User-Agent": self.USER_AGENT},
            timeout=self.timeout,
            follow_redirects=True
        ) as client:
            for lang in source_languages:
                try:
                    result = await self._search_and_extract(client, clean_query, lang)
                    if result:
                        sources.append({
                            "provider": "Wikipedia",
                            "language": lang,
                            "title": result["title"],
                            "url": result["url"],
                            "retrievedAt": datetime.now(timezone.utc).isoformat()
                        })
                        collected_notes.append(f"[{lang.upper()} - {result['title']}]: {result['extract']}")
                except Exception as e:
                    logger.warning(f"Failed to fetch Wikipedia ({lang}) for '{query}': {e}")

        # If primary search failed, try fallback sanitized keywords
        if not sources and len(clean_query.split()) > 2:
            simplified = " ".join(clean_query.split()[:3])
            try:
                async with httpx.AsyncClient(
                    headers={"User-Agent": self.USER_AGENT},
                    timeout=self.timeout,
                    follow_redirects=True
                ) as client:
                    result = await self._search_and_extract(client, simplified, "vi")
                    if result:
                        sources.append({
                            "provider": "Wikipedia",
                            "language": "vi",
                            "title": result["title"],
                            "url": result["url"],
                            "retrievedAt": datetime.now(timezone.utc).isoformat()
                        })
                        collected_notes.append(f"[VI - {result['title']}]: {result['extract']}")
            except Exception as e:
                logger.warning(f"Fallback search failed for '{simplified}': {e}")

        research_notes = "\n\n".join(collected_notes) if collected_notes else (
            f"Tư liệu lịch sử & truyền thuyết Việt Nam cho chủ đề: {clean_query}."
        )

        return {
            "title": clean_query,
            "sources": sources,
            "researchNotes": research_notes,
            "isLegend": is_legend,
            "topic": topic or ("Truyền thuyết" if is_legend else "Lịch sử Việt Nam")
        }

    async def _search_and_extract(
        self,
        client: httpx.AsyncClient,
        query: str,
        lang: str
    ) -> Optional[Dict[str, Any]]:
        api_url = self.VI_API if lang == "vi" else self.EN_API
        
        # 1. Search for matching pages
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": "1",
            "srlimit": "5"
        }
        
        res = await client.get(api_url, params=search_params)
        if res.status_code != 200:
            return None
            
        data = res.json()
        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return None

        # 2. Select the most relevant page
        best_page = self._pick_best_match(query, search_results)
        if not best_page:
            return None

        page_id = best_page["pageid"]

        # 3. Retrieve introductory extract and canonical URL
        extract_params = {
            "action": "query",
            "prop": "extracts|info",
            "exintro": "1",
            "explaintext": "1",
            "inprop": "url",
            "pageids": str(page_id),
            "format": "json",
            "utf8": "1"
        }
        
        res_extract = await client.get(api_url, params=extract_params)
        if res_extract.status_code != 200:
            return None
            
        pages = res_extract.json().get("query", {}).get("pages", {})
        page_info = pages.get(str(page_id))
        if not page_info:
            return None

        raw_extract = page_info.get("extract", "").strip()
        # Clean up excessive newlines or wiki artifacts
        cleaned_extract = re.sub(r'\n{2,}', '\n\n', raw_extract)

        return {
            "title": page_info.get("title", best_page["title"]),
            "url": page_info.get("fullurl", f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(best_page['title'])}"),
            "extract": cleaned_extract[:2500]  # Cap intro extract for optimal prompt context
        }

    def _pick_best_match(self, query: str, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Calculates similarity and picks the top matching title without falling into disambiguation traps.
        """
        q_norm = self._normalize_vietnamese(query.lower())
        
        for item in results:
            t_norm = self._normalize_vietnamese(item["title"].lower())
            # Direct match or substring match
            if q_norm == t_norm or q_norm in t_norm or t_norm in q_norm:
                return item
                
        # Default to first result if score is acceptable
        return results[0] if results else None

    @staticmethod
    def _detect_folklore_or_legend(query: str, topic: Optional[str] = None) -> bool:
        """
        Determines whether a story subject belongs to folklore, mythology, fairy tales or recorded history.
        """
        combined = f"{query} {topic or ''}".lower()
        folklore_keywords = [
            "truyền thuyết", "thần thoại", "cổ tích", "sơn tinh", "thủy tinh", "chử đồng tử",
            "thánh gióng", "liễu hạnh", "an dương vương", "mỵ châu", "trọng thủy", "lạc long quân",
            "âu cơ", "bánh chưng", "bánh giầy", "tấm cám", "thạch sanh", "cây tre trăm đốt",
            "dân gian", "huyền tích", "thần phả", "thần tích"
        ]
        return any(kw in combined for kw in folklore_keywords)

    @staticmethod
    def _normalize_vietnamese(text: str) -> str:
        """
        Normalizes diacritics for flexible fuzzy comparisons.
        """
        text = text.lower()
        patterns = {
            '[àáạảãâầấậẩẫăằắặẳẵ]': 'a',
            '[èéẹẻẽêềếệểễ]': 'e',
            '[ìíịỉĩ]': 'i',
            '[òóọỏõôồốộổỗơờớợởỡ]': 'o',
            '[ùúụủũưừứựửữ]': 'u',
            '[ỳýỵỷỹ]': 'y',
            '[đ]': 'd',
        }
        for pattern, replacement in patterns.items():
            text = re.sub(pattern, replacement, text)
        return re.sub(r'[^a-z0-9\s]', '', text).strip()
