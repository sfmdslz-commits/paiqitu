#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排期表生成核心（网站版）。
与 skill 独立；所有字体均为 SIL Open Font License 1.1 开源商用字体：
  - Noto Serif CJK SC（思源宋体）：标题、剧名、印章
  - Noto Sans CJK SC（思源黑体）：正文、表头、同场演员
背景图为原创水墨风格。无任何商用授权风险。
"""
import os, re, datetime, urllib.request, urllib.parse, io

HERE = os.path.dirname(os.path.abspath(__file__))
BG = os.path.join(HERE, "assets", "bg.png")

# 字体：全部 SIL OFL 1.1 商用授权，保持不变
SERIF = '"Noto Serif CJK SC","Source Han Serif SC",serif'
SANS = '"Noto Sans CJK SC","Source Han Sans SC",sans-serif'

# 中式低饱和配色主题（不同色相），色值取自传统色意象并降低饱和度。
THEMES = {
    "qinglv": {
        "label": "青绿 · 烟波", "desc": "沉静青绿，原版配色",
        "ink": "#234B4E", "deep": "#2C6B6B", "mid": "#3E8A88", "teal": "#6FB0AC",
        "pale": "#A9D2CD", "base": "#DFEEE9", "paper": "rgba(255,255,255,0.82)",
        "grid": "rgba(169,210,205,0.8)", "shade": "rgba(169,210,205,0.18)",
        "weekend": "#9C5A3C", "dnum": "rgba(62,138,136,0.42)", "shadow": "rgba(35,75,78,0.14)",
        "veil": "linear-gradient(180deg, rgba(231,244,242,.55), rgba(238,247,245,.32) 40%, rgba(228,242,239,.58))",
        "palette": ["#2C6B6B","#3E8A88","#4A6E86","#8A6E3E","#6B4E6E","#4E6E52","#8A5A4E","#5E6E8A"],
    },
    "tongdai": {
        "label": "铜黛 · 沉金", "desc": "铜色含黛，金属沉静",
        "ink": "#43382C", "deep": "#6B5638", "mid": "#8C7247", "teal": "#B49A6A",
        "pale": "#D8C9A8", "base": "#EFE7D6", "paper": "rgba(255,252,244,0.84)",
        "grid": "rgba(180,154,106,0.7)", "shade": "rgba(216,201,168,0.22)",
        "weekend": "#8C4A3C", "dnum": "rgba(140,114,71,0.42)", "shadow": "rgba(67,56,44,0.13)",
        "veil": "linear-gradient(180deg, rgba(246,238,221,.55), rgba(250,245,232,.32) 40%, rgba(242,233,214,.58))",
        "palette": ["#6B5638","#8C7247","#7A6A52","#9A8050","#5E5140","#8A6A42","#6E6250","#A08A5E"],
    },
    "ouhe": {
        "label": "藕荷 · 烟霞", "desc": "浅粉含灰，烟霞藕荷",
        "ink": "#4A3540", "deep": "#7A5566", "mid": "#A87688", "teal": "#C9A0AE",
        "pale": "#E4CBD4", "base": "#F3E8EC", "paper": "rgba(255,250,252,0.84)",
        "grid": "rgba(201,160,174,0.66)", "shade": "rgba(228,203,212,0.22)",
        "weekend": "#9C6A5A", "dnum": "rgba(168,118,136,0.42)", "shadow": "rgba(74,53,64,0.13)",
        "veil": "linear-gradient(180deg, rgba(248,238,242,.55), rgba(252,247,249,.32) 40%, rgba(242,231,236,.58))",
        "palette": ["#7A5566","#A87688","#9A6E7E","#B08393","#8E6680","#B78A78","#93708A","#A67E8E"],
    },
    "qinghua": {
        "label": "青花 · 鎏金", "desc": "浅蓝瓷底与鎏金撞色，金色只作描边点缀",
        # 大面积：浅蓝白瓷底 + 极淡金晕染（蓝金撞色但都保持浅色）
        "ink": "#20486B", "deep": "#2E5C82", "mid": "#6E8AA8", "teal": "#C9B181",
        "pale": "#E8EEF5", "base": "#EEF3F6", "paper": "rgba(255,255,255,0.90)",
        "grid": "rgba(46,92,130,0.32)", "shade": "rgba(201,177,129,0.14)",
        "weekend": "#B99B63", "dnum": "rgba(32,72,107,0.40)", "shadow": "rgba(32,72,107,0.14)",
        "veil": "linear-gradient(135deg, rgba(228,240,249,.60), rgba(250,245,231,.40) 55%, rgba(226,238,247,.60))",
        "palette": ["#20486B","#A79165","#3A6B96","#C9B181","#2E5C82","#9E8760","#517FA8","#D2BD96"],
        # 鎏金点缀：表头蓝底金字 + 深蓝边框 + 淡金标题/印章（不用于大面积底色）
        "headbg": "#2E5C82", "headfg": "#F3E6C4", "framec": "#2E5C82",
        "border": "#2E5C82", "gold": "#CBA96C",
    },
    "meimei": {
        "label": "墨莓 · 绛紫", "desc": "深色含香，沉静莓紫",
        "ink": "#3A2E3C", "deep": "#5E425E", "mid": "#7E5A7E", "teal": "#AB86A6",
        "pale": "#D6BED2", "base": "#EEE5ED", "paper": "rgba(255,251,255,0.84)",
        "grid": "rgba(171,134,166,0.62)", "shade": "rgba(214,190,210,0.2)",
        "weekend": "#9C5A4E", "dnum": "rgba(126,90,126,0.42)", "shadow": "rgba(58,46,60,0.13)",
        "veil": "linear-gradient(180deg, rgba(244,236,243,.55), rgba(250,245,250,.32) 40%, rgba(238,229,237,.58))",
        "palette": ["#5E425E","#7E5A7E","#6B587E","#8E5A6E","#5A5A7E","#9A6A5E","#7E6A8E","#8E7086"],
    },
    "feiyan": {
        "label": "绯岩 · 赭石", "desc": "岩色起伏，温润赭红",
        "ink": "#423330", "deep": "#6E4940", "mid": "#926251", "teal": "#BC8C74",
        "pale": "#DEC0AE", "base": "#F2E9E1", "paper": "rgba(255,252,249,0.84)",
        "grid": "rgba(188,140,116,0.62)", "shade": "rgba(222,192,174,0.22)",
        "weekend": "#5E6E8A", "dnum": "rgba(146,98,81,0.42)", "shadow": "rgba(66,51,48,0.13)",
        "veil": "linear-gradient(180deg, rgba(248,239,232,.55), rgba(252,247,242,.32) 40%, rgba(244,234,225,.58))",
        "palette": ["#6E4940","#926251","#8A5A50","#A97458","#7E5A48","#B08268","#8E6E5E","#9E7E6A"],
    },
    "hupiao": {
        "label": "湖缥 · 远山", "desc": "湖光缥缈，淡蓝远山",
        "ink": "#2C3E4E", "deep": "#3E6280", "mid": "#5A86A6", "teal": "#8AB4CC",
        "pale": "#BBD6E4", "base": "#E4EEF4", "paper": "rgba(252,254,255,0.84)",
        "grid": "rgba(138,180,204,0.68)", "shade": "rgba(187,214,228,0.2)",
        "weekend": "#A8684E", "dnum": "rgba(90,134,166,0.42)", "shadow": "rgba(44,62,78,0.13)",
        "veil": "linear-gradient(180deg, rgba(232,242,248,.55), rgba(242,249,252,.32) 40%, rgba(226,238,246,.58))",
        "palette": ["#3E6280","#5A86A6","#5E7E9E","#6E8E88","#7E7EA6","#8E7E5E","#5E8EA6","#8AA0BE"],
    },
    "yezhan": {
        "label": "夜绀 · 黛蓝", "desc": "深蓝藏青，静谧夜色",
        "ink": "#26303E", "deep": "#384C6E", "mid": "#526A92", "teal": "#8098BC",
        "pale": "#B4C2D8", "base": "#E2E8F0", "paper": "rgba(251,253,255,0.84)",
        "grid": "rgba(128,152,188,0.66)", "shade": "rgba(180,194,216,0.2)",
        "weekend": "#A26A58", "dnum": "rgba(82,106,146,0.42)", "shadow": "rgba(38,48,62,0.13)",
        "veil": "linear-gradient(180deg, rgba(234,239,246,.55), rgba(243,246,251,.32) 40%, rgba(228,235,244,.58))",
        "palette": ["#384C6E","#526A92","#4E6E8E","#6E6292","#5A6E86","#8A7E5E","#6E7EA2","#7A8EAA"],
    },
}
DEFAULT_THEME = "qinglv"


def get_theme(key):
    return THEMES.get(key) or THEMES[DEFAULT_THEME]
CN_NUM = {1:"壹",2:"贰",3:"叁",4:"肆",5:"伍",6:"陆",7:"柒",8:"捌",9:"玖",10:"拾",
          11:"拾壹",12:"拾贰"}
MONTH_EN = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
            7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}


def fetch(url):
    if not re.match(r"^https?://", url or ""):
        raise ValueError("网址必须以 http:// 或 https:// 开头")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def normalize_artist_url(url):
    """把各种形式的演员页链接归一化为可解析数据的规范 URL（必须带 other/musical 参数）。"""
    url = (url or "").strip()
    if re.match(r"^\d+$", url):
        return f"https://y.saoju.net/yyj/artist/{url}/?other=1&musical="
    m = re.search(r"/yyj/artist/(\d+)/", url)
    if m:
        aid = m.group(1)
        return f"https://y.saoju.net/yyj/artist/{aid}/?other=1&musical="
    return url


def search_artists(keyword):
    """按演员姓名在 saoju.net 搜索，返回候选列表 [{name, url}]。"""
    keyword = (keyword or "").strip()
    if not keyword:
        raise ValueError("请输入演员姓名")
    # 若用户直接粘贴了网址，直接归一化返回
    if re.match(r"^https?://", keyword):
        url = normalize_artist_url(keyword)
        if "/yyj/artist/" not in url:
            raise ValueError("网址不是演员排期页，应形如 y.saoju.net/yyj/artist/2168/")
        return [{"name": "", "url": url}]
    q = urllib.parse.quote(keyword)
    page = fetch(f"https://y.saoju.net/yyj/search/?q={q}")
    cands, seen = [], set()
    for m in re.finditer(r'href="(/yyj/artist/(\d+)/)"[^>]*>(.*?)</a>', page):
        aid = m.group(2)
        nm = re.sub(r"<[^>]+>", "", m.group(3)).strip()
        if aid in seen:
            continue
        seen.add(aid)
        cands.append({"name": nm or f"演员{aid}", "url": normalize_artist_url(aid)})
    return cands


def _infer_year(mo):
    """主页日期不含年份：>= 当前月视为今年，否则视为明年（沿用原逻辑）。"""
    today = datetime.date.today()
    return today.year if mo >= today.month else today.year + 1


def parse_artist_page(page_html):
    """解析主页演出（未来场次，日期无年份）。返回 (name, rows)，row=(year,mo,d,t,drama,role,co,loc)。"""
    m = re.search(r"<title>(.*?)</title>", page_html, re.S)
    name = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else "演员"
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", page_html, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 5:
            continue
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", td)).strip() for td in tds[:5]]
        date_s, drama, role, co, loc = cells
        dm = re.match(r"(\d{1,2})月(\d{1,2})日", date_s)
        if not dm:
            continue
        mo, d = int(dm.group(1)), int(dm.group(2))
        tm = re.search(r"(\d{1,2}:\d{2})", date_s)
        rows.append((_infer_year(mo), mo, d, tm.group(1) if tm else "",
                     drama, role, co, loc))
    return name, rows


def parse_past_page(page_html):
    """解析 /show 过往演出页（已完成场次，日期带年份）。兼容 4 列与 5 列（含同场演员）。"""
    ths = [re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", th))
           for th in re.findall(r"<th[^>]*>(.*?)</th>", page_html, re.S)]
    has_co = any("同场演员" in t for t in ths)
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", page_html, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 4:
            continue
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", td)).strip() for td in tds[:5]]
        date_s, drama, role = cells[0], cells[1], cells[2]
        if has_co and len(cells) >= 5:
            co, loc = cells[3], cells[4]
        else:
            co, loc = "", cells[3]
        dm = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_s)
        if not dm:
            continue
        y, mo, d = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
        tm = re.search(r"(\d{1,2}:\d{2})", date_s)
        rows.append((y, mo, d, tm.group(1) if tm else "",
                     drama, role, co, loc))
    return rows


def past_page_count(page_html):
    """从过往演出页的分页菜单里取最大页码。"""
    nums = [int(n) for n in re.findall(r"[?&]page=(\d+)", page_html)]
    return max(nums) if nums else 1


def fetch_all(url):
    """抓取主页 + 过往演出页全部分页，合并去重，返回 (name, rows)。rows 含已完成演出。"""
    url = normalize_artist_url(url)
    main_html = fetch(url)
    name, rows = parse_artist_page(main_html)
    m = re.search(r"/yyj/artist/(\d+)/", url)
    if m:
        past_base = f"https://y.saoju.net/yyj/artist/{m.group(1)}/show"
        try:
            # 带 other=1 可拿到同场演员列；第一页同时用于探测总页数
            first = fetch(past_base + "?page=1&other=1")
            rows += parse_past_page(first)
            total = past_page_count(first)
            for pg in range(2, total + 1):
                try:
                    rows += parse_past_page(fetch(past_base + f"?page={pg}&other=1"))
                except Exception:
                    continue
        except Exception:
            try:
                rows += parse_past_page(fetch(past_base))
            except Exception:
                pass  # 过往页抓取失败则只用主页数据
    # 去重（同年月日 + 时间 + 剧名 + 角色），同键优先保留带同场演员的版本
    # 注意：key 必须含时间，否则「同一天午晚同剧目同角色、仅时间/同场演员不同」的场次会被误合并
    seen, uniq = {}, []
    for r in rows:
        key = (r[0], r[1], r[2], r[3], r[4], r[5])
        if key not in seen:
            seen[key] = len(uniq)
            uniq.append(r)
        elif r[6] and not uniq[seen[key]][6]:
            uniq[seen[key]] = r
    uniq.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
    return name, uniq


def decide_month(rows, month_arg):
    if month_arg:
        m = re.match(r"^(\d{4})-(\d{1,2})$", month_arg.strip())
        if not m:
            raise ValueError("月份格式应为 YYYY-MM，例如 2026-12")
        return int(m.group(1)), int(m.group(2))
    today = datetime.date.today()
    counts = {}
    for y, mo, d, t, drama, role, co, loc in rows:
        counts[(y, mo)] = counts.get((y, mo), 0) + 1
    if not counts:
        return today.year, today.month
    # 优先靠近当月的未来月份，其次场次多
    best = sorted(counts.items(),
                  key=lambda kv: (abs(kv[0][0]-today.year)*12+abs(kv[0][1]-today.month), -kv[1]))[0][0]
    return best


def available_months(rows):
    seen = {}
    for y, mo, d, t, drama, role, co, loc in rows:
        k = f"{y}-{mo:02d}"
        seen[k] = seen.get(k, 0) + 1
    return sorted(seen.items(), key=lambda kv: kv[0])


def shorten_location(loc):
    parts = re.split(r"\s+", loc.strip())
    city = parts[0] if parts else ""
    rest = " ".join(parts[1:]) if len(parts) > 1 else ""
    theater = rest.split("·")[-1].strip() if rest else ""
    for redundant in ["国际艺术交流中心", "艺术交流中心", "文化交流中心", "国际文化中心",
                      "国际艺术中心", "艺术中心", "文化中心", "国际"]:
        theater = theater.replace(redundant, "")
    theater = theater.strip("· ")
    result = f"{city}·{theater}" if city and theater else (city or theater or loc)
    # 去「主剧场/小剧场/大剧场」等细分后缀；剧场名本身已含城市时视为完整固定名称
    # （如「上海文化广场」「南京保利大剧院」），直接用，不再拆成「城市·剧场」
    if "·" in result:
        c, t = result.split("·", 1)
        for suf in ("主剧场", "小剧场", "大剧场"):
            if t.endswith(suf):
                t = t[:-len(suf)]
        t = t.strip("· ")
        if t.startswith(c):
            return t
        return f"{c}·{t}" if t else c
    return result


def shorten_co(co, drama):
    names = co.strip().split()
    if not names:
        return ""
    if len(names) > 3:
        # 超过3人：只显示前两位，后面用「等」
        return "& " + " ".join(names[:2]) + "等"
    # 3人及以下：全部显示，允许换行（见 .ev-with 的 white-space:normal）
    return "& " + " ".join(names)


def build(data, year, month, theme=None, bg_path=None, show_summary=False, show_co=True, grid_opacity=1.0):
    th = theme or THEMES[DEFAULT_THEME]
    INK, DEEP, MID, TEAL, PALE = th["ink"], th["deep"], th["mid"], th["teal"], th["pale"]
    PAPER, GRID, SHADE = th["paper"], th["grid"], th["shade"]
    WEEKEND, DNUM, SHADOW = th["weekend"], th["dnum"], th["shadow"]
    VEIL, PALETTE = th["veil"], th["palette"]
    # 可选：鎏金主题把「金色」从 deep 中解耦，仅用于表头字、边框、标题与印章
    HEADBG = th.get("headbg", DEEP)   # 表头底色
    HEADFG = th.get("headfg", PALE)   # 表头文字色
    FRAMEC = th.get("framec", PALE)   # 内嵌线框色
    BORDER = th.get("border", TEAL)   # 日历外框色
    GOLD   = th.get("gold", DEEP)     # 副标题「X月排期」字色
    # 日历格不透明度：只让日历格底板/表头/演出填色按比例透明，文字不受影响，底图可透出
    try:
        grid_op = max(0.0, min(1.0, float(grid_opacity)))
    except (TypeError, ValueError):
        grid_op = 1.0
    def _rgba(hexc, a):
        h = hexc.lstrip('#')
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        try:
            return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"
        except ValueError:
            return hexc
    paper_c = PAPER if grid_op >= 1.0 else _rgba(PAPER, grid_op)
    headbg_c = HEADBG if grid_op >= 1.0 else _rgba(HEADBG, grid_op)
    shade_c = SHADE if grid_op >= 1.0 else _rgba(SHADE, grid_op)
    name, raw_rows = data
    evs_by_day = {}
    for y, mo, d, t, drama, role, co, loc in raw_rows:
        if y != year or mo != month:
            continue
        evs_by_day.setdefault(d, []).append((t, drama, role, shorten_location(loc), shorten_co(co, drama)))
    drama_order = []
    for d in sorted(evs_by_day):
        for e in evs_by_day[d]:
            if e[1] not in drama_order:
                drama_order.append(e[1])
    C = {dn: PALETTE[i % len(PALETTE)] for i, dn in enumerate(drama_order)}
    summary = []
    for dn in drama_order:
        k = sum(1 for d in evs_by_day for e in evs_by_day[d] if e[1] == dn)
        summary.append((dn, k))
    total = sum(k for _, k in summary)
    # 底部总结条：按「剧名 + 角色」分别统计场次，同一部剧的不同角色都列出
    role_summary = []
    for dn in drama_order:
        rc = {}
        for d in evs_by_day:
            for e in evs_by_day[d]:
                if e[1] == dn:
                    r = (e[2] or "").strip()
                    rc[r] = rc.get(r, 0) + 1
        role_summary.append((dn, list(rc.items())))

    first_wd = datetime.date(year, month, 1).weekday()
    ndays = (datetime.date(year + (month == 12), month % 12 + 1, 1) - datetime.date(year, month, 1)).days
    cells = [None] * first_wd + list(range(1, ndays + 1))
    while len(cells) % 7:
        cells.append(None)

    def cell_html(day):
        if day is None:
            return '<div class="cell empty"></div>'
        evlist = evs_by_day.get(day)
        if not evlist:
            return f'<div class="cell"><span class="dnum">{day}</span></div>'
        multi = len(evlist) > 1
        parts = [f'<span class="dnum">{day}</span>']
        for t, drama, role, loc, co in evlist:
            col = C[drama]
            loc_fs = 14 if len(loc) <= 8 else (11 if len(loc) <= 10 else (10 if len(loc) <= 13 else 9))
            co_html = " ".join(f'<span class="wn">{"&amp;" if w == "&" else w}</span>' for w in co.split(" ")) if co else ""
            with_html = f'<span class="ev-with" style="--c:{col}">{co_html}</span>' if (show_co and co_html) else ""
            if multi:
                parts.append(
                    f'<div class="event multi" style="--c:{col}; --locfs:{min(loc_fs,10)}px">'
                    f'<span class="ev-time">{t}</span>'
                    f'<span class="ev-name">{drama}</span>'
                    f'<span class="ev-role">饰 {role}</span>'
                    f'<span class="ev-loc">{loc}</span>'
                    f'{with_html}'
                    f'</div>'
                )
            else:
                parts.append(
                    f'<div class="event" style="--c:{col}; --locfs:{loc_fs}px">'
                    f'<span class="ev-time">{t}</span>'
                    f'<span class="ev-name">{drama}</span>'
                    f'<span class="ev-role">饰 {role}</span>'
                    f'<span class="ev-loc">{loc}</span>'
                    f'</div>'
                    f'{with_html}'
                )
        return '<div class="cell has-ev' + (' multi-cell' if multi else '') + '">' + "".join(parts) + "</div>"

    rows = "".join(
        '<div class="row">' + "".join(cell_html(d) for d in cells[i:i+7]) + "</div>"
        for i in range(0, len(cells), 7)
    )
    sum_html = "".join(
        f'<div class="sum-chip" style="--c:{C[n]}"><span>{n}</span><b>x{k}</b></div>'
        for n, k in summary
    )
    title = f"{name}{month}月排期"
    eyebrow = f"{MONTH_EN.get(month, month)}.{year}"
    tmain = name
    tsub = f"{month}月排期"
    # 表格内部分割线：主题墨色的 40% 透明度实线
    _h = INK.lstrip("#")
    line40 = f"rgba({int(_h[0:2],16)},{int(_h[2:4],16)},{int(_h[4:6],16)},0.4)"
    sum_label = f"{CN_NUM.get(month, month)}月演出总结"
    n_drama = len(drama_order)
    sum_num = f"{n_drama} 部剧 · 共 {total} 场"

    # 演出总结放到整个月历下方：全宽、小字、40% 透明度，剧名之间用竖线分隔
    cal_title_top = 264
    cal_top = cal_title_top + 46
    calendar_bottom = cal_top + 1010
    if show_summary:
        sum_h = 44
        summary_top = calendar_bottom + 16
        bar = '<span class="sum-bar">|</span>'
        def _role_seg(n, rc):
            # 同一剧多角色都写：夜雨他时 苏轼x1 苏辙x2；单角色：夜雨他时 苏轼x5
            parts = " ".join(f'{r}x{c}' for r, c in rc if r)
            return f'{n} {parts}' if parts else f'{n} x{sum(c for _, c in rc)}'
        items = bar.join(f'<span class="sum-item">{_role_seg(n, rc)}</span>' for n, rc in role_summary)
        summary_html = (f'<div class="summary"><span class="sum-label">{sum_label}</span>{bar}'
                        f'{items}{bar}<span class="sum-total">共 {total} 场</span></div>')
        body_h = calendar_bottom + sum_h + 90
    else:
        sum_h = 0
        summary_top = calendar_bottom
        summary_html = ""
        body_h = calendar_bottom + 77

    # 背景层：纯色底；若提供底图，则以 30% 透明度叠加其上
    bg_layer = ""
    if bg_path:
        bg_layer = (f'<div class="usercover" style="background-image:url(\'file://{bg_path}\')"></div>')

    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ width:1000px; height:{body_h}px; position:relative; overflow:hidden;
    background:{th['base']}; font-family:{SERIF}; color:{INK}; }}
  .usercover {{ position:absolute; inset:0; background-size:cover; background-position:center;
    background-repeat:no-repeat; opacity:.30; }}
  .veil {{ position:absolute; inset:0; background:{VEIL}; }}
  .frame {{ position:absolute; inset:22px; border:2px solid {FRAMEC}; border-radius:8px; pointer-events:none; opacity:.5; }}
  .header {{ position:absolute; left:52px; top:44px; right:52px; height:196px;
    display:flex; justify-content:space-between; align-items:flex-start; }}
  .htitle {{ display:flex; flex-direction:column; gap:2px; }}
  .eyebrow {{ font-family:{SERIF}; font-size:20px; font-weight:700; letter-spacing:8px; color:{MID}; }}
  .t-main {{ font-family:{SERIF}; font-size:80px; font-weight:900; line-height:1.05; letter-spacing:1px; color:{INK};
    text-shadow:2px 3px 0 rgba(255,255,255,.75); }}
  .t-sub {{ font-family:{SERIF}; font-size:58px; font-weight:900; line-height:1.05; letter-spacing:3px; color:{GOLD};
    text-shadow:2px 2px 0 rgba(255,255,255,.7); }}
  .t-name {{ font-family:{SERIF}; font-size:54px; font-weight:900; line-height:1; letter-spacing:8px; color:{DEEP};
    text-shadow:2px 2px 0 rgba(255,255,255,.7); }}
  .seal {{ width:112px; height:112px; margin-top:6px; border:5px double {GOLD}; border-radius:8px;
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    color:{GOLD}; transform:rotate(5deg); background:rgba(255,255,255,.35); }}
  .seal .big {{ font-family:{SERIF}; font-size:38px; font-weight:900; letter-spacing:6px; }}
  .seal .sm {{ font-family:{SANS}; font-size:12px; font-weight:700; letter-spacing:2px; margin-top:4px; }}
  .summary {{ position:absolute; left:52px; right:52px; top:{summary_top}px; height:{sum_h}px;
    display:flex; align-items:center; justify-content:center; flex-wrap:wrap; gap:6px 14px;
    font-family:{SANS}; font-size:19px; font-weight:700; color:{INK}; opacity:.4; }}
  .summary .sum-label {{ font-family:{SERIF}; font-size:23px; font-weight:900; letter-spacing:2px; }}
  .summary .sum-bar {{ color:{TEAL}; font-weight:900; }}
  .summary .sum-total {{ font-weight:900; }}
  .cal-title {{ position:absolute; left:52px; right:52px; top:{cal_title_top}px; height:38px;
    display:flex; align-items:center; gap:16px; font-family:{SERIF}; font-weight:900;
    font-size:26px; letter-spacing:5px; color:{DEEP}; }}
  .cal-title .ln {{ flex:1; height:2px; background:{PALE}; }}
  .calendar {{ position:absolute; left:52px; right:52px; top:{cal_top}px; height:1010px;
    background:{paper_c}; border:2px solid {BORDER}; border-radius:10px; overflow:hidden;
    box-shadow:0 8px 22px {SHADOW}; }}
  .headrow {{ display:grid; grid-template-columns:repeat(7,1fr); height:60px;
    background:{headbg_c}; border-bottom:2px solid {BORDER}; }}
  .headrow .h {{ display:flex; align-items:center; justify-content:center;
    font-family:{SANS}; font-size:24px; font-weight:900; letter-spacing:3px; color:{HEADFG};
    border-right:1px solid {line40}; }}
  .headrow .h:last-child {{ border-right:none; }}
  .row {{ display:grid; grid-template-columns:repeat(7,1fr); height:190px; }}
  .row:not(:last-child) {{ border-bottom:1px solid {line40}; }}
  .cell {{ position:relative; padding:12px 9px; border-right:1px solid {line40}; overflow:hidden; }}
  .cell:last-child {{ border-right:none; }}
  .cell.has-ev {{ background:{shade_c}; }}
  .cell:nth-child(6) .dnum::after, .cell:nth-child(7) .dnum::after {{ content:"";
    position:absolute; right:-5px; top:-2px; width:5px; height:5px; border-radius:50%; background:{WEEKEND}; }}
  .dnum {{ position:absolute; right:11px; top:8px; font-family:{SANS}; font-size:17px; font-weight:700;
    color:{DNUM}; }}
  .cell.has-ev .dnum {{ font-size:21px; font-weight:900; color:{INK}; }}
  .event {{ margin-top:20px; display:flex; flex-direction:column; align-items:flex-start; text-align:left; gap:7px; }}
  /* 四类信息用字体+字重+透明度区分，颜色仍在主题色系内保持和谐 */
  .ev-name {{ font-family:{SERIF}; font-size:20px; font-weight:900; color:var(--c); line-height:1.12; }}
  .ev-role {{ font-family:{SANS}; font-size:15px; font-weight:700; color:{INK}; line-height:1.15;
    white-space:normal; word-break:break-all; }}
  .ev-time {{ font-family:{SANS}; font-size:14px; font-weight:800; color:var(--c); line-height:1.1; text-align:left; opacity:.6; }}
  .ev-loc {{ font-family:{SANS}; font-size:13px; font-weight:500; color:{INK}; line-height:1.2; text-align:center;
    white-space:nowrap; max-width:100%; opacity:.5; }}
  .cell:not(.multi-cell) .ev-loc{{ margin-top:2px; }}
  .ev-with {{ position:static; display:block; margin-top:3px; text-align:left; font-family:{SANS};
    font-size:12px; font-weight:600; color:var(--c); line-height:1.25; white-space:normal; overflow-wrap:break-word; opacity:.7; }}
  .cell:not(.multi-cell) .ev-with{{ font-size:9px; line-height:1.2; margin-top:5px; }}
  .ev-with .wn {{ display:inline-block; white-space:nowrap; }}
  .cell.multi-cell {{ padding-top:9px; }}
  .event.multi {{ margin-top:1px; gap:3px; }}
  .event.multi + .event.multi{{ margin-top:8px; border-top:1px dashed rgba(46,92,130,.3); padding-top:7px; }}
  .event.multi .ev-time {{ font-size:11px; }}
  .event.multi .ev-name {{ font-size:13px; }}
  .event.multi .ev-role {{ font-size:11px; }}
  .event.multi .ev-loc{{ font-size:10px; }}
  .event.multi .ev-with {{ position:static; display:block; font-size:9px; line-height:1.15; margin-top:1px; }}
  .foot {{ position:absolute; left:52px; right:52px; bottom:36px; font-family:{SANS};
    font-size:13px; font-weight:600; color:{DEEP}; opacity:.55; display:flex; justify-content:space-between; }}
</style></head><body>
  {bg_layer}<div class="veil"></div><div class="frame"></div>
  <div class="header">
    <div class="htitle">
      <div class="eyebrow">{eyebrow}</div>
      <div class="t-main">{tmain}</div>
      <div class="t-sub">{tsub}</div>
    </div>
    <div class="seal"><div class="big">排期</div><div class="sm">SCHEDULE</div></div>
  </div>
  <div class="cal-title"><span>本月演出档期</span><span class="ln"></span></div>
  <div class="calendar">
    <div class="headrow">
      <div class="h">一</div><div class="h">二</div><div class="h">三</div>
      <div class="h">四</div><div class="h">五</div>
      <div class="h we">六</div><div class="h we">日</div>
    </div>
    {rows}
  </div>
  {summary_html}
  <div class="foot"><span>数据：saoju.net 演员排期</span><span>角色及同场演员以现场为准</span></div>
</body></html>"""
    return html, title, total, name, year, month


def render(html, out_png):
    tmp = os.path.join(os.path.dirname(out_png), ".cal_render_web.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--no-sandbox", "--allow-file-access-from-files",
                                    "--font-render-hinting=none"])
        try:
            m = re.search(r"body\s*\{\s*width:1000px;\s*height:(\d+)px", html)
            page_h = int(m.group(1)) if m else 1565
            pg = b.new_page(viewport={"width": 1000, "height": page_h}, device_scale_factor=2)
            pg.goto("file://" + tmp)
            # 等待系统字体就绪（思源宋体/黑体为系统字体，无需网络加载）
            pg.evaluate("() => document.fonts.ready")
            pg.wait_for_timeout(1200)
            pg.screenshot(path=out_png, full_page=True)
        finally:
            b.close()
    if os.path.exists(tmp):
        os.remove(tmp)
    return out_png


def generate(url, month=None, out_png=None, theme=None, bg_path=None, extra_rows=None, show_summary=False, show_co=True, grid_opacity=1.0):
    data = fetch_all(url)
    name, raw = data
    if extra_rows:
        raw = raw + list(extra_rows)
        # 去重（同年月日 + 时间 + 剧名 + 角色），避免同日午晚同剧目被误合并
        seen, uniq = set(), []
        for r in raw:
            key = (r[0], r[1], r[2], r[3], r[4], r[5])
            if key in seen:
                continue
            seen.add(key)
            uniq.append(r)
        raw = uniq
        data = (name, raw)
    if not raw:
        raise ValueError("未在该页面解析到演出数据，请确认网址是演员排期页（形如 y.saoju.net/yyj/artist/<id>/?other=1&musical=）")
    year, mo = decide_month(raw, month)
    html, title, total, name, year, mo = build(data, year, mo, theme=get_theme(theme), bg_path=bg_path,
                                               show_summary=show_summary, show_co=show_co,
                                               grid_opacity=grid_opacity)
    if out_png is None:
        out_png = os.path.join(HERE, ".tmp_output", f"{name}_{year}{mo:02d}.png")
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    # 顺带保存 HTML（零渲染开销），供「导出分层 PNG 包」按需复用，避免重复抓取
    with open(os.path.splitext(out_png)[0] + ".html", "w", encoding="utf-8") as _f:
        _f.write(html)
    render(html, out_png)
    return {"name": name, "year": year, "month": mo, "total": total, "path": out_png}


def manual_entries_to_rows(year, month, entries):
    """把前端手动补充的场次转换为统一 row 结构 (year,mo,d,t,drama,role,co,loc)。"""
    rows = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        try:
            day = int(e.get("day"))
            datetime.date(year, month, day)
        except Exception:
            raise ValueError("补充场次日期无效，请检查日号是否正确")
        t = (e.get("time") or "").strip()
        drama = (e.get("drama") or "").strip()
        role = (e.get("role") or "").strip()
        co = (e.get("co") or "").strip()
        loc = (e.get("loc") or "").strip()
        if not drama:
            raise ValueError("补充场次的剧目名称不能为空")
        rows.append((year, month, day, t, drama, role, co, loc))
    return rows


# ---- 分层 PNG 导出：底图 / 日历格(含边框) / 文字，三层透明叠加可还原原图 ----
_LAYER_HIDE_TEXT = """
.eyebrow,.t-main,.t-sub,.t-name,.seal .big,.seal .sm,.h,.dnum,
.ev-name,.ev-role,.ev-time,.ev-loc,.ev-with,.summary,.cal-title>span:first-child,.foot span
{ color:transparent !important; text-shadow:none !important; }
"""
_LAYER_HIDE_SEAL = ".seal{ display:none !important; }\n"
_LAYER_HIDE_DOT = ".cell:nth-child(6) .dnum::after,.cell:nth-child(7) .dnum::after{ display:none !important; }\n"

LAYER_CSS = {
    # 纯底图：背景色、晕染、用户底图；不含边框/格线/文字
    "1_底图": """
.frame{ display:none !important; }
.calendar{ background:transparent !important; border-color:transparent !important; box-shadow:none !important; }
.headrow{ background:transparent !important; border-color:transparent !important; }
.cal-title .ln{ background:transparent !important; }
.cell,.row:not(:last-child),.headrow .h{ border-color:transparent !important; }
.cell.has-ev{ background:transparent !important; }
""" + _LAYER_HIDE_DOT + _LAYER_HIDE_TEXT + _LAYER_HIDE_SEAL,
    # 日历格（含边框）：外框、日历容器底与外框、表头深底、内部格线、演出日填充、周末圆点、标题横线
    "2_日历格含边框": """
body{ background:transparent !important; }
.usercover,.veil{ display:none !important; }
""" + _LAYER_HIDE_TEXT + _LAYER_HIDE_SEAL,
    # 文字：标题、印章、表头字、日期数字、四类演出信息、总结、页脚
    "3_文字": """
body{ background:transparent !important; }
.usercover,.veil,.frame{ display:none !important; }
.calendar{ background:transparent !important; border-color:transparent !important; box-shadow:none !important; }
.headrow{ background:transparent !important; border-color:transparent !important; }
.cell,.row:not(:last-child),.headrow .h{ border-color:transparent !important; }
.cell.has-ev{ background:transparent !important; }
.cal-title .ln{ background:transparent !important; }
""" + _LAYER_HIDE_DOT,
}

LAYER_ORDER = ("1_底图", "2_日历格含边框", "3_文字")


def render_layers(html, out_dir):
    """把成图 HTML 渲染成三层透明 PNG，返回 (名称, 路径) 列表。主题无关。"""
    os.makedirs(out_dir, exist_ok=True)
    m = re.search(r"body\s*\{\s*width:1000px;\s*height:(\d+)px", html)
    page_h = int(m.group(1)) if m else 1565
    tmp = os.path.join(out_dir, ".layer_render.html")
    results = []
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--no-sandbox", "--allow-file-access-from-files",
                                    "--font-render-hinting=none"])
        try:
            for key in LAYER_ORDER:
                h = html.replace("</head>",
                                 f"<style class='layer-export'>{LAYER_CSS[key]}</style></head>")
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(h)
                pg = b.new_page(viewport={"width": 1000, "height": page_h}, device_scale_factor=2)
                try:
                    pg.goto("file://" + tmp)
                    pg.evaluate("() => document.fonts.ready")
                    pg.wait_for_timeout(600)
                    out = os.path.join(out_dir, key + ".png")
                    pg.screenshot(path=out, full_page=True, omit_background=True)
                    results.append((key, out))
                finally:
                    pg.close()
        finally:
            b.close()
    if os.path.exists(tmp):
        os.remove(tmp)
    return results
