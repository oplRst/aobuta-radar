import json, os, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as f:
    config = json.load(f)

def clean(value):
    return re.sub(r"\\s+", " ", value or "").strip() 
AOBUTA_TERMS = [
    # 作品名・略称
    "青春ブタ野郎",
    "青ブタ",
    "青春ブタ野郎はバニーガール先輩の夢を見ない",
    "青春ブタ野郎は夢見る少女の夢を見ない",
    "青春ブタ野郎はお出かけシスターの夢を見ない",
    "青春ブタ野郎はランドセルガールの夢を見ない",
    "青春ブタ野郎はディアフレンドの夢を見ない",
    "ディアフレンド",
    "たゆたうクラゲ",

    # キャラクター名
    "桜島麻衣",
    "梓川咲太",
    "古賀朋絵",
    "双葉理央",
    "豊浜のどか",
    "梓川花楓",
    "牧之原翔子",
    "広川卯月",
    "赤城郁実",
    "姫路紗良",
    "美東美織",
    "岩見沢寧々",

    # 原作・イラスト関係
    "鴨志田一",
    "溝口ケージ",

    # 声優
    "石川界人",
    "瀬戸麻沙美",
    "雨宮天",
    "山根綺",
    "小原好美",
    "石見舞菜香",
    "上田麗奈",
    "東山奈央",
    "種﨑敦美",
    "内田真礼",
    "久保ユリカ",
    "水瀬いのり"
]

def is_aobuta_related(title):
    return any(term in title for term in AOBUTA_TERMS)

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
            if not is_aobuta_related(title): continue   
            pub = clean(node.findtext("pubDate"))
            try: pub = parsedate_to_datetime(pub).isoformat() if pub else ""
            except Exception: pass
            items.append({"title":title,"url":link,"published":pub,"source":clean(node.findtext("source")) or "Google News RSS","category":group.get("label","ニュース")})
    except Exception as exc:
        errors.append({"category":group.get("label",""),"error":str(exc)})

dedup = {}
for item in items:
    key = item["url"]
    if key not in dedup:
        dedup[key] = item
    else:
        old = dedup[key]
        if item["category"] not in old["category"]:
            old["category"] += "・" + item["category"]

title_dedup = {}
for item in dedup.values():
    key = item["title"].strip()
    if key not in title_dedup:
        title_dedup[key] = item
    else:
        old = title_dedup[key]
        if item["category"] not in old["category"]:
            old["category"] += "・" + item["category"]

items = sorted(
    title_dedup.values(),
    key=lambda x: x.get("published", ""),
    reverse=True
)[:150]
print("保存:",len(items),"件 / エラー:",len(errors),"件")
