from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from .models import NewsArticleRecord, QuerySpec


_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

_REPUTATION_KEYWORDS = {
    "boycott", "grève", "plainte", "rappel", "controverse", "polémique", "fermeture",
    "licenciement", "sanction", "fraude", "crise", "accident"
}
_CX_KEYWORDS = {
    "sav", "service client", "retour", "remboursement", "avis", "attente", "livraison", "magasin"
}
_BENCHMARK_KEYWORDS = {"vs", "ou", "comparatif", "benchmark", "face à", "face a"}
_PRODUCT_KEYWORDS = {"vtt", "vélo", "velo", "rockrider", "btwin", "van rysel", "quechua", "produit", "lance"}
_STORE_KEYWORDS = {"ouvre", "ouvre", "ouverture", "ferme", "fermeture", "magasin", "store", "city"}
_SPORTS_TEAM_KEYWORDS = {
    "cma cgm", "cma-cgm", "cyclisme", "cyclist", "tour down under", "paris-nice", "tirreno",
    "uci", "étape", "etape", "sprinteur", "grimpeur", "prolonge", "peloton", "classement uci"
}


def parse_rss_feed(xml_text: str) -> tuple[str, list[ET.Element]]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    title = channel.findtext("title", default="") if channel is not None else ""
    items = channel.findall("item") if channel is not None else []
    return title, items


def _strip_tags(value: str) -> str:
    text = _TAG_RE.sub(" ", value or "")
    text = html.unescape(text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _classify_signal(text: str) -> str:
    lowered = text.lower()
    if any(keyword in lowered for keyword in _REPUTATION_KEYWORDS):
        return "reputation"
    if any(keyword in lowered for keyword in _BENCHMARK_KEYWORDS) and "decathlon" in lowered and "intersport" in lowered:
        return "benchmark"
    if any(keyword in lowered for keyword in _STORE_KEYWORDS):
        return "store_network"
    if any(keyword in lowered for keyword in _CX_KEYWORDS):
        return "cx"
    if any(keyword in lowered for keyword in _SPORTS_TEAM_KEYWORDS):
        return "sports_team"
    if any(keyword in lowered for keyword in _PRODUCT_KEYWORDS):
        return "product"
    return "general"


def _detect_brand(text: str, brand_focus: str) -> str:
    lowered = text.lower()
    has_decathlon = "decathlon" in lowered
    has_intersport = "intersport" in lowered
    if has_decathlon and has_intersport:
        return "both"
    if has_decathlon:
        return "decathlon"
    if has_intersport:
        return "intersport"
    return brand_focus


def _parse_published_at(raw_value: str) -> str:
    if not raw_value:
        return ""
    try:
        return parsedate_to_datetime(raw_value).isoformat()
    except Exception:
        return raw_value


def build_article_record(run_id: str, spec: QuerySpec, item: ET.Element) -> NewsArticleRecord:
    title = (item.findtext("title", default="") or "").strip()
    description_html = item.findtext("description", default="") or ""
    description_text = _strip_tags(description_html)
    source_el = item.find("source")
    source_name = (source_el.text or "").strip() if source_el is not None and source_el.text else ""
    source_url = source_el.attrib.get("url", "") if source_el is not None else ""
    source_domain = urlparse(source_url).netloc
    if source_name:
        source_pattern = re.compile(rf"{re.escape(source_name)}\s*$", re.IGNORECASE)
        description_text = source_pattern.sub("", description_text).strip(" -:\u00a0")
    body_for_classification = " ".join(part for part in [title, description_text] if part)
    article_id = (item.findtext("guid", default="") or item.findtext("link", default="") or title).strip()
    return NewsArticleRecord(
        run_id=run_id,
        query_name=spec.name,
        query_text=spec.query_text,
        query_names=[spec.name],
        brand_focus=spec.brand_focus,
        source_brand_focuses=[spec.brand_focus],
        article_id=article_id,
        article_title=title,
        published_at=_parse_published_at(item.findtext("pubDate", default="") or ""),
        source_name=source_name,
        source_domain=source_domain,
        google_news_url=(item.findtext("link", default="") or "").strip(),
        description_html=description_html,
        description_text=description_text,
        signal_type=_classify_signal(body_for_classification),
        brand_detected=_detect_brand(body_for_classification, spec.brand_focus),
    )


def merge_article(existing: NewsArticleRecord, incoming: NewsArticleRecord) -> NewsArticleRecord:
    if incoming.query_name not in existing.query_names:
        existing.query_names.append(incoming.query_name)
    if incoming.brand_focus not in existing.source_brand_focuses:
        existing.source_brand_focuses.append(incoming.brand_focus)
    if existing.brand_detected != incoming.brand_detected:
        existing.brand_detected = "both"
    if not existing.source_name and incoming.source_name:
        existing.source_name = incoming.source_name
    if not existing.source_domain and incoming.source_domain:
        existing.source_domain = incoming.source_domain
    if incoming.signal_type == "benchmark":
        existing.signal_type = "benchmark"
    elif existing.signal_type == "general" and incoming.signal_type != "general":
        existing.signal_type = incoming.signal_type
    if not existing.description_text and incoming.description_text:
        existing.description_text = incoming.description_text
    return existing


def is_relevant_article(article: NewsArticleRecord) -> bool:
    text = " ".join(
        part for part in [article.article_title, article.description_text, article.source_name] if part
    ).lower()
    if article.brand_detected == "both":
        return True
    if article.signal_type != "sports_team":
        return True
    if "intersport" in text:
        return True
    return False
