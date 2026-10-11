import json, os, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as f:
    config = json.load(f)

def clean(value):
    return re.sub(r"\\s+", " ", value or "").strip()

items, errors = [], []
for group in config.get("queries", []):
    try:
        url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(group["query"]) + "&hl=ja&gl=JP&ceid=JP:ja"
        req = urllib.request.Request(url, headers={"User-Agent": "AobutaRadar/1.0"})
        with urllib.request.urlopen(req, timeout=25) as response:
            root = ET.fromstring(response.read())
        for node in root.findall(".//item"):
            title, link = clean(node.findtext("title")), clean(node.findtext("link"))
            if not title or not link: continue
            pub = clean(node.findtext("pubDate"))
            try: pub = parsedate_to_datetime(pub).isoformat() if pub else ""
            except Exception: pass
            items.append({"title":title,"url":link,"published":pub,"source":clean(node.findtext("source")) or "Google News RSS","category":group.get("label","ニュース")})
    except Exception as exc:
        errors.append({"category":group.get("label",""),"error":str(exc)})

dedup = {}
for item in items:
    if item["url"] not in dedup: dedup[item["url"]] = item
    elif item["category"] not in dedup[item["url"]]["category"]:
        dedup[item["url"]]["category"] += "・" + item["category"]
items = sorted(dedup.values(), key=lambda x:x.get("published",""), reverse=True)[:150]
payload = {"updated_at":datetime.now(timezone.utc).isoformat(),"count":len(items),"items":items,"errors":errors}
os.makedirs(os.path.join(ROOT,"data"),exist_ok=True)
with open(os.path.join(ROOT,"data","news.json"),"w",encoding="utf-8") as f:
    json.dump(payload,f,ensure_ascii=False,indent=2)
print("保存:",len(items),"件 / エラー:",len(errors),"件")
