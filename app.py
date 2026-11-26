#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""saoju.net 演员排期表一键排版网站（独立产物，全商用授权字体）。"""
import os, uuid, re, threading, datetime, io, zipfile
from flask import Flask, request, render_template, jsonify, send_file, abort

import generator

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "outputs")
UPLOAD_DIR = os.path.join(HERE, "uploads")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_BG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

app = Flask(__name__)
_lock = threading.Lock()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/themes", methods=["GET"])
def api_themes():
    """返回可选的中式配色主题。"""
    items = [{"key": k, "label": v["label"], "desc": v["desc"],
              "swatches": [v["ink"], v["deep"], v["mid"], v["teal"], v["pale"], v["base"]]}
             for k, v in generator.THEMES.items()]
    return jsonify(ok=True, themes=items, default=generator.DEFAULT_THEME)


@app.route("/api/upload-bg", methods=["POST"])
def api_upload_bg():
    """上传自定义底图，返回 token 供排版时引用。"""
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(ok=False, error="请选择图片文件"), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_BG_EXT:
        return jsonify(ok=False, error="仅支持 PNG / JPG / WEBP / BMP / GIF 图片"), 400
    token = uuid.uuid4().hex[:12]
    path = os.path.join(UPLOAD_DIR, token + ext)
    f.save(path)
    return jsonify(ok=True, token=token, filename=f.filename)


@app.route("/api/bg/<token>")
def api_bg(token):
    if not re.match(r"^[0-9a-f]{12}$", token):
        abort(404)
    for ext in ALLOWED_BG_EXT:
        p = os.path.join(UPLOAD_DIR, token + ext)
        if os.path.exists(p):
            return send_file(p)
    abort(404)


@app.route("/api/search", methods=["POST"])
def api_search():
    """输入演员姓名，返回候选演员（含可直接抓取的规范网址）。"""
    data = request.get_json(silent=True) or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        return jsonify(ok=False, error="请输入演员姓名"), 400
    try:
        cands = generator.search_artists(keyword)
        if not cands:
            return jsonify(ok=False, error=f"没有搜到名为「{keyword}」的演员，请检查姓名或改用网址"), 404
        return jsonify(ok=True, candidates=cands)
    except Exception as e:
        return jsonify(ok=False, error=f"搜索失败：{e}"), 400


@app.route("/api/preview", methods=["POST"])
def api_preview():
    """抓取网址，返回演员名与可选月份列表（不渲染图片）。"""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify(ok=False, error="请填写演员排期网址"), 400
    url = generator.normalize_artist_url(url)
    try:
        name, rows = generator.fetch_all(url)
        if not rows:
            return jsonify(ok=False, error="未解析到演出数据，请确认网址是 y.saoju.net 的演员排期页"), 400
        months = [{"value": k, "label": f"{k[:4]}年{int(k[5:7])}月", "count": c}
                  for k, c in generator.available_months(rows)]
        auto_y, auto_m = generator.decide_month(rows, None)
        # 查询当日的上月 / 本月 / 下月三个选项
        today = datetime.date.today()
        def shift(y, m, delta):
            idx = y * 12 + (m - 1) + delta
            return idx // 12, idx % 12 + 1
        month_counts = dict(generator.available_months(rows))
        around = []
        for delta, tag in ((-1, "上月"), (0, "本月"), (1, "下月")):
            y, m = shift(today.year, today.month, delta)
            key = f"{y}-{m:02d}"
            around.append({"value": key, "tag": tag,
                           "label": f"{y}年{m}月", "count": month_counts.get(key, 0)})
        # 返回全部场次明细，供前端做「按月份分组」的场次编辑（改字段/删场/加场）
        rows_json = [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]] for r in rows]
        return jsonify(ok=True, name=name, months=months, around=around,
                       auto=f"{auto_y}-{auto_m:02d}", total_rows=len(rows), rows=rows_json)
    except Exception as e:
        return jsonify(ok=False, error=f"抓取失败：{e}"), 400


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    month = (data.get("month") or "").strip() or None
    theme = (data.get("theme") or "").strip() or None
    bg_token = (data.get("bg_token") or "").strip() or None
    show_summary = bool(data.get("show_summary", False))
    show_co = bool(data.get("show_co", True))
    try:
        grid_opacity = float(data.get("grid_opacity", 1.0))
    except (TypeError, ValueError):
        grid_opacity = 1.0
    if not url:
        return jsonify(ok=False, error="请填写演员排期网址"), 400
    url = generator.normalize_artist_url(url)
    bg_path = None
    if bg_token and re.match(r"^[0-9a-f]{12}$", bg_token):
        for ext in ALLOWED_BG_EXT:
            p = os.path.join(UPLOAD_DIR, bg_token + ext)
            if os.path.exists(p):
                bg_path = p
                break
    try:
        with _lock:
            token = uuid.uuid4().hex[:12]
            out = os.path.join(OUT_DIR, f"{token}.png")
            result = generator.generate(url, month=month, out_png=out, theme=theme, bg_path=bg_path,
                                        show_summary=show_summary, show_co=show_co,
                                        grid_opacity=grid_opacity)
        fname = f"{result['name']}_{result['year']}年{result['month']}月排期.png"
        return jsonify(ok=True, token=token, filename=fname,
                       name=result["name"], year=result["year"], month=result["month"],
                       total=result["total"], download=f"/api/download/{token}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400


@app.route("/api/generate-supplement", methods=["POST"])
def api_generate_supplement():
    """在 saoju 查询结果基础上，并入手动补充的场次后排版导出排期表。"""
    import datetime as _dt
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    month = (data.get("month") or "").strip() or None
    theme = (data.get("theme") or "").strip() or None
    bg_token = (data.get("bg_token") or "").strip() or None
    show_summary = bool(data.get("show_summary", False))
    show_co = bool(data.get("show_co", True))
    try:
        grid_opacity = float(data.get("grid_opacity", 1.0))
    except (TypeError, ValueError):
        grid_opacity = 1.0
    if not url:
        return jsonify(ok=False, error="请先查询演员"), 400
    if not month or not re.match(r"^\d{4}-\d{1,2}$", month):
        return jsonify(ok=False, error="请选择有效的月份"), 400
    entries = data.get("entries") or []
    if not isinstance(entries, list) or not entries:
        return jsonify(ok=False, error="请至少填写一场补充演出"), 400
    y, m = int(month.split("-")[0]), int(month.split("-")[1])
    try:
        extra_rows = generator.manual_entries_to_rows(y, m, entries)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400
    url = generator.normalize_artist_url(url)
    bg_path = None
    if bg_token and re.match(r"^[0-9a-f]{12}$", bg_token):
        for ext in ALLOWED_BG_EXT:
            p = os.path.join(UPLOAD_DIR, bg_token + ext)
            if os.path.exists(p):
                bg_path = p
                break
    try:
        with _lock:
            token = uuid.uuid4().hex[:12]
            out = os.path.join(OUT_DIR, f"{token}.png")
            result = generator.generate(url, month=month, out_png=out,
                                        theme=theme, bg_path=bg_path, extra_rows=extra_rows,
                                        show_summary=show_summary, show_co=show_co,
                                        grid_opacity=grid_opacity)
        fname = f"{result['name']}_{result['year']}年{result['month']}月排期.png"
        return jsonify(ok=True, token=token, filename=fname,
                       name=result["name"], year=result["year"], month=result["month"],
                       total=result["total"], download=f"/api/download/{token}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400


@app.route("/api/generate-manual", methods=["POST"])
def api_generate_manual():
    """手动录入演出排版导出排期表（用于 saoju.net 没有排期的情况）。"""
    import datetime as _dt
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(ok=False, error="请填写演员姓名"), 400
    try:
        year = int(data.get("year"))
        month = int(data.get("month"))
        _dt.date(year, month, 1)
    except Exception:
        return jsonify(ok=False, error="请选择有效的年月"), 400
    entries = data.get("entries") or []
    if not isinstance(entries, list) or not entries:
        return jsonify(ok=False, error="请至少添加一场演出"), 400
    rows = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        try:
            day = int(e.get("day"))
            _dt.date(year, month, day)
        except Exception:
            return jsonify(ok=False, error="演出日期无效，请检查日号是否正确"), 400
        t = (e.get("time") or "").strip()
        drama = (e.get("drama") or "").strip()
        role = (e.get("role") or "").strip()
        co = (e.get("co") or "").strip()
        loc = (e.get("loc") or "").strip()
        if not drama:
            return jsonify(ok=False, error="剧目名称不能为空"), 400
        rows.append((year, month, day, t, drama, role, co, loc))
    if not rows:
        return jsonify(ok=False, error="请至少添加一场有效演出"), 400

    theme = (data.get("theme") or "").strip() or None
    bg_token = (data.get("bg_token") or "").strip() or None
    show_co = bool(data.get("show_co", True))
    try:
        grid_opacity = float(data.get("grid_opacity", 1.0))
    except (TypeError, ValueError):
        grid_opacity = 1.0
    bg_path = None
    if bg_token and re.match(r"^[0-9a-f]{12}$", bg_token):
        for ext in ALLOWED_BG_EXT:
            p = os.path.join(UPLOAD_DIR, bg_token + ext)
            if os.path.exists(p):
                bg_path = p
                break
    try:
        with _lock:
            token = uuid.uuid4().hex[:12]
            out = os.path.join(OUT_DIR, f"{token}.png")
            html, title, total, rname, y, m = generator.build(
                (name, rows), year, month, theme=generator.get_theme(theme), bg_path=bg_path,
                show_co=show_co, grid_opacity=grid_opacity)
            with open(os.path.splitext(out)[0] + ".html", "w", encoding="utf-8") as _f:
                _f.write(html)
            generator.render(html, out)
        fname = f"{name}_{year}年{month}月排期.png"
        return jsonify(ok=True, token=token, filename=fname,
                       name=name, year=year, month=month, total=total,
                       download=f"/api/download/{token}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400


@app.route("/api/generate-rows", methods=["POST"])
def api_generate_rows():
    """用编辑后的完整场次明细直接排版导出（不重新抓 saoju），供「场次管理」使用。"""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(ok=False, error="缺少演员姓名"), 400
    month = (data.get("month") or "").strip()
    if not re.match(r"^\d{4}-\d{1,2}$", month):
        return jsonify(ok=False, error="请选择有效的月份"), 400
    year, mo = int(month.split("-")[0]), int(month.split("-")[1])
    rows_in = data.get("rows") or []
    if not isinstance(rows_in, list) or not rows_in:
        return jsonify(ok=False, error="没有可排版的场次"), 400
    rows = []
    for e in rows_in:
        try:
            y, m, d = int(e[0]), int(e[1]), int(e[2])
        except (TypeError, ValueError, IndexError):
            continue
        if y != year or m != mo:
            continue
        t = str(e[3] or "").strip() if len(e) > 3 else ""
        drama = str(e[4] or "").strip() if len(e) > 4 else ""
        role = str(e[5] or "").strip() if len(e) > 5 else ""
        co = str(e[6] or "").strip() if len(e) > 6 else ""
        loc = str(e[7] or "").strip() if len(e) > 7 else ""
        if not drama:
            continue
        rows.append((y, m, d, t, drama, role, co, loc))
    if not rows:
        return jsonify(ok=False, error="所选月份没有有效场次"), 400
    rows.sort(key=lambda r: (r[2], r[3]))
    theme = (data.get("theme") or "").strip() or None
    bg_token = (data.get("bg_token") or "").strip() or None
    show_summary = bool(data.get("show_summary", False))
    show_co = bool(data.get("show_co", True))
    try:
        grid_opacity = float(data.get("grid_opacity", 1.0))
    except (TypeError, ValueError):
        grid_opacity = 1.0
    bg_path = None
    if bg_token and re.match(r"^[0-9a-f]{12}$", bg_token):
        for ext in ALLOWED_BG_EXT:
            p = os.path.join(UPLOAD_DIR, bg_token + ext)
            if os.path.exists(p):
                bg_path = p
                break
    try:
        with _lock:
            token = uuid.uuid4().hex[:12]
            out = os.path.join(OUT_DIR, f"{token}.png")
            html, title, total, rname, y, m = generator.build(
                (name, rows), year, mo, theme=generator.get_theme(theme), bg_path=bg_path,
                show_summary=show_summary, show_co=show_co, grid_opacity=grid_opacity)
            with open(os.path.splitext(out)[0] + ".html", "w", encoding="utf-8") as _f:
                _f.write(html)
            generator.render(html, out)
        fname = f"{name}_{year}年{mo}月排期.png"
        return jsonify(ok=True, token=token, filename=fname, name=name, year=year, month=mo,
                       total=total, download=f"/api/download/{token}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400


@app.route("/api/layers/<token>")
def api_layers(token):
    """按需把已排版好的排期图拆成三层透明 PNG 并打包下载（不影响默认排版速度）。"""
    if not re.match(r"^[0-9a-f]{12}$", token):
        abort(404)
    html_path = os.path.join(OUT_DIR, f"{token}.html")
    if not os.path.exists(html_path):
        abort(404)
    with open(html_path, encoding="utf-8") as _f:
        html = _f.read()
    layer_dir = os.path.join(OUT_DIR, f"{token}_layers")
    with _lock:
        rendered = generator.render_layers(html, layer_dir)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for key, path in rendered:
            z.write(path, arcname=key + ".png")
        z.writestr("分层说明.txt",
                   "分层 PNG 说明\n"
                   "============\n"
                   "三层均为透明背景，尺寸一致，按下面顺序叠加即可还原完整成图。\n\n"
                   "Photoshop 图层顺序（从下到上）：\n"
                   "  1_底图.png          背景底色、晕染、自定义底图\n"
                   "  2_日历格含边框.png  日历表格与外框、表头底、格线、填充、周末圆点\n"
                   "  3_文字.png          标题、印章、表头字、日期、剧目/角色/时间/剧场/同场演员\n\n"
                   "说明：文字层为像素图，可整体编辑/换色，但不能双击改字；\n"
                   "      若要可编辑文字需另导出 SVG 或分层 PSD。\n")
    buf.seek(0)
    dlname = request.args.get("name", "排期图") + "_分层包.zip"
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=dlname)


@app.route("/api/download/<token>")
def api_download(token):
    if not re.match(r"^[0-9a-f]{12}$", token):
        abort(404)
    path = os.path.join(OUT_DIR, f"{token}.png")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype="image/png", as_attachment=True,
                     download_name=request.args.get("name", "排期表.png"))


@app.route("/api/image/<token>")
def api_image(token):
    if not re.match(r"^[0-9a-f]{12}$", token):
        abort(404)
    path = os.path.join(OUT_DIR, f"{token}.png")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype="image/png")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")))
    args = ap.parse_args()
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
