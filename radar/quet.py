"""Thu thập ứng viên ý tưởng cho kênh Dr Lizzi.

  python radar/quet.py [--dry]

Nguồn:
  * YouTube Data API v3 (YOUTUBE_API_KEY): video 14 ngày gần nhất theo từ khóa VN/EN + câu hỏi trong bình luận.
  * Google Trends VN qua pytrends (không chính thức, lỗi thì bỏ qua).
  * TikTok qua TikNeuron (TIKNEURON_API_KEY): 1 lượt tìm, chỉ thứ Hai (giờ VN), tự dừng khi hết credit.
Kết quả: out/ung-vien.json. Không cần thư viện ngoài, trừ pytrends (tùy chọn).
--dry: không gọi mạng, dùng dữ liệu giả để chạy thử luồng.
"""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "radar" / "tu-khoa.json").read_text(encoding="utf-8"))
STATE_P = ROOT / "state" / "da-thay.json"
OUT = ROOT / "out"
DRY = "--dry" in sys.argv
VN = timezone(timedelta(hours=7))
NOW = datetime.now(timezone.utc)
YT = "https://www.googleapis.com/youtube/v3"
QWORDS = re.compile(r"\?|sao|không|có nên|bao lâu|bao nhiêu|làm sao|thế nào|được không|how|why|should|does|is it|can i", re.I)


def log(*a):
    print(*a, flush=True)


def load_state():
    if STATE_P.exists():
        return json.loads(STATE_P.read_text(encoding="utf-8"))
    return {}


UA = "Mozilla/5.0 (compatible; drlizzi-radar/1.0)"  # Cloudflare của TikNeuron chặn User-Agent mặc định "Python-urllib"


def get(url, headers=None, timeout=30):
    h = {"Accept": "application/json", "User-Agent": UA, **(headers or {})}
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# ---------------- YouTube ----------------
def yt(path, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    return get(f"{YT}/{path}?{urllib.parse.urlencode(params)}")


def youtube(state, seen):
    if DRY:
        return [{"src": "youtube", "lang": "vi", "kw": "trị nám", "id": "dry1", "title": "Trị nám bằng laser có hết không?",
                 "channel": "Kênh A", "url": "https://www.youtube.com/watch?v=dry1", "views": 250000, "age_days": 5,
                 "views_per_day": 50000, "questions": ["Laser xong có bị tái không bác sĩ?", "Bao lâu thì đỡ?"]},
                {"src": "youtube", "lang": "en", "kw": "hair loss after pregnancy", "id": "dry2",
                 "title": "Postpartum hair loss: when does it stop?", "channel": "Derm B",
                 "url": "https://www.youtube.com/watch?v=dry2", "views": 900000, "age_days": 9,
                 "views_per_day": 100000, "questions": ["Is minoxidil safe while breastfeeding?"]}]
    if not os.environ.get("YOUTUBE_API_KEY"):
        log("Bỏ qua YouTube: chưa có YOUTUBE_API_KEY"); return []
    lim = CFG["gioi_han"]
    kws = [("vi", k) for k in CFG["youtube_vi"]] + [("en", k) for k in CFG["youtube_en"]]
    start = state.get("kw_index", 0) % max(1, len(kws))
    pick = (kws[start:] + kws[:start])[:lim["youtube_luot_tim_moi_ngay"]]
    state["kw_index"] = (start + len(pick)) % max(1, len(kws))
    after = (NOW - timedelta(days=lim["so_ngay_gan_day"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = {}
    for lang, kw in pick:
        try:
            p = dict(part="snippet", q=kw, type="video", order="viewCount", publishedAfter=after,
                     maxResults=lim["ket_qua_moi_luot"], relevanceLanguage=lang)
            if lang == "vi":
                p["regionCode"] = "VN"
            res = yt("search", **p)
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode("utf-8", "replace")
            log(f"YouTube lỗi {e.code} khi tìm '{kw}': {body}")
            if e.code == 403:
                break  # hết hạn mức hoặc key sai: dừng cả nguồn YouTube
            continue
        for it in res.get("items", []):
            vid = it["id"].get("videoId")
            if vid and vid not in seen and vid not in found:
                found[vid] = {"src": "youtube", "lang": lang, "kw": kw, "id": vid,
                              "title": it["snippet"]["title"], "channel": it["snippet"]["channelTitle"],
                              "url": f"https://www.youtube.com/watch?v={vid}",
                              "published": it["snippet"]["publishedAt"]}
    ids = list(found)
    for i in range(0, len(ids), 50):
        try:
            res = yt("videos", part="statistics", id=",".join(ids[i:i + 50]))
        except urllib.error.HTTPError as e:
            log("YouTube lỗi khi lấy thống kê:", e.code); break
        for it in res.get("items", []):
            v = found[it["id"]]
            v["views"] = int(it["statistics"].get("viewCount", 0))
            pub = datetime.strptime(v["published"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            v["age_days"] = max(1, (NOW - pub).days)
            v["views_per_day"] = v["views"] // v["age_days"]
    vids = [v for v in found.values()
            if v.get("views", 0) >= (lim["view_toi_thieu_vi"] if v["lang"] == "vi" else lim["view_toi_thieu_en"])]
    vids.sort(key=lambda v: v["views_per_day"], reverse=True)
    for v in vids[:lim["video_lay_binh_luan"]]:
        try:
            res = yt("commentThreads", part="snippet", videoId=v["id"], order="relevance", maxResults=40,
                     textFormat="plainText")
            qs = [c["snippet"]["topLevelComment"]["snippet"]["textDisplay"][:200] for c in res.get("items", [])]
            v["questions"] = [q for q in qs if QWORDS.search(q)][:5]
        except urllib.error.HTTPError:
            v["questions"] = []  # bình luận bị tắt
    log(f"YouTube: {len(pick)} lượt tìm, {len(found)} video mới, {len(vids)} đạt ngưỡng view")
    return vids


# ---------------- Google Trends ----------------
def trends():
    if DRY:
        return [{"src": "google_trends", "kw": "rụng tóc", "rising": [["rụng tóc sau sinh", "+250%"]]}]
    try:
        from pytrends.request import TrendReq
    except ImportError:
        log("Bỏ qua Google Trends: chưa cài pytrends"); return []
    out = []
    try:
        # không truyền retries/backoff_factor: pytrends 4.9 dùng tham số cũ 'method_whitelist' mà urllib3 2.x đã bỏ
        py = TrendReq(hl="vi-VN", tz=-420, timeout=(10, 25))
        kws = CFG["trends_vi"]
        for i in range(0, len(kws), 5):
            py.build_payload(kws[i:i + 5], timeframe="now 7-d", geo="VN")
            rel = py.related_queries()
            for kw, d in rel.items():
                r = d.get("rising") if d else None
                if r is not None and len(r):
                    out.append({"src": "google_trends", "kw": kw,
                                "rising": [[str(q), f"+{v}%" if isinstance(v, (int, float)) else str(v)]
                                           for q, v in r.head(5).values.tolist()]})
    except Exception as e:  # pytrends hay bị Google chặn: không làm hỏng cả lần chạy
        log("Google Trends lỗi, bỏ qua:", str(e)[:200])
    log(f"Google Trends: {len(out)} từ khóa có truy vấn tăng")
    return out


# ---------------- TikTok (TikNeuron) ----------------
def tiktok(state, seen):
    t = state.setdefault("tiktok", {"credits_used": 0, "kw_index": 0, "stopped": False, "last": ""})
    today = datetime.now(VN)
    force = "--tiktok" in sys.argv
    if DRY:
        return []
    if not os.environ.get("TIKNEURON_API_KEY"):
        log("Bỏ qua TikTok: chưa có TIKNEURON_API_KEY"); return []
    if t["stopped"]:
        log("Bỏ qua TikTok: đã dừng vì hết credit hoặc bị từ chối (sửa 'stopped' trong state để chạy lại)"); return []
    if t["credits_used"] >= CFG["gioi_han"]["tiktok_credit_toi_da"]:
        log("Bỏ qua TikTok: đã dùng hết số credit cho phép"); return []
    if not force and (today.weekday() != 0 or t["last"] == today.strftime("%Y-%m-%d")):
        log("Bỏ qua TikTok: chỉ chạy thứ Hai"); return []
    kws = CFG["tiktok"]
    kw = kws[t["kw_index"] % len(kws)]
    url = "https://tikneuron.com/api/mcp/search?" + urllib.parse.urlencode({"query": kw})
    try:
        data = get(url, {"MCP-API-KEY": os.environ["TIKNEURON_API_KEY"], "Accept": "application/json"}, timeout=60)
    except urllib.error.HTTPError as e:
        log(f"TikTok lỗi {e.code}: {e.read()[:200].decode('utf-8', 'replace')}")
        if e.code in (401, 402, 403, 429):
            t["stopped"] = True
        return []
    except Exception as e:
        log("TikTok lỗi:", str(e)[:200]); return []
    t["credits_used"] += 1
    t["kw_index"] += 1
    t["last"] = today.strftime("%Y-%m-%d")
    out = []
    for v in data.get("videos") or []:
        vid = str(v.get("video_id", ""))
        if not vid or vid in seen:
            continue
        def num(x):
            try:
                return int(float(str(x).replace(",", "")))
            except ValueError:
                return 0
        out.append({"src": "tiktok", "lang": "?", "kw": kw, "id": vid, "title": (v.get("description") or "")[:200],
                    "channel": v.get("creator", ""), "url": f"https://www.tiktok.com/@{v.get('creator', '')}/video/{vid}",
                    "views": num(v.get("views")), "likes": num(v.get("likes")), "comments": num(v.get("comments")),
                    "hashtags": v.get("hashtags", [])[:8]})
    out.sort(key=lambda v: v["views"], reverse=True)
    log(f"TikTok: tìm '{kw}', {len(out)} video, đã dùng {t['credits_used']} credit")
    return out[:15]


def main():
    state = load_state()
    seen = set(state.get("videos", []))
    yt_v = youtube(state, seen)
    tr = trends()
    tk = tiktok(state, seen)
    cap = CFG["gioi_han"]["ung_vien_toi_da"]
    cands = {"date": datetime.now(VN).strftime("%Y-%m-%d"), "videos": (yt_v[:cap] + tk)[:cap + 15], "trends": tr}
    OUT.mkdir(exist_ok=True)
    (OUT / "ung-vien.json").write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "state-moi.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Xong: {len(cands['videos'])} video, {len(tr)} nhóm trend → out/ung-vien.json")


if __name__ == "__main__":
    main()
