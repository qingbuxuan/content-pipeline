# -*- coding: utf-8 -*-
"""内容流水线：节点函数 + Flask 路由"""
from config import *
from html_converter import *
from utils import *
from wechat import *
from prompts import *
from feishu import push_to_feishu

def get_weekday_theme():
    weekday = beijing_now().weekday()
    theme_info = WEEKLY_THEMES.get(weekday, WEEKLY_THEMES[0])
    log(f"[主题] 今天{WEEKDAY_NAMES[weekday]} · {theme_info['name']} · {theme_info['theme']}")
    return weekday, theme_info

def read_articles(weekday, limit=4):
    """从飞书读取最近几周同主题文章"""
    from datetime import timedelta
    try:
        token = get_feishu_token()
        if not token:
            return ""
        table_id = FEISHU_BITABLE_TABLE_ID
        weekday_name = WEEKDAY_NAMES[weekday]
        # Get records (filter in Python to avoid encoding issues)
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/records"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        data = resp.json()
        if data.get("code") != 0:
            return ""
        items = data.get("data", {}).get("items", [])
        if not items:
            return ""
        # Filter by weekday in Python
        articles = []
        for item in items:
            fields = item.get("fields", {})
            wk = fields.get("星期", "")
            if wk == weekday_name:
                body = fields.get("正文", "") or ""
                if body and len(body) > 50:
                    articles.append(body[:500])
        return "\n\n".join(articles[:limit])
    except Exception as e:
        log(f"[防重复] 读取失败: {e}")
        return ""

    log(f"[主题] 今天{WEEKDAY_NAMES[weekday]} · {theme_info['name']} · {theme_info['theme']}")
    return weekday, theme_info

def score_item(title, theme_keywords=None):
    score = 0
    for kw in KEYWORDS:
        if kw in title:
            score += 1
    if theme_keywords:
        for kw in theme_keywords:
            if kw in title:
                score += 3
    return score

def node1_collector():
    weekday, theme_info = get_weekday_theme()
    theme_keywords = theme_info["keywords"]
    theme_name = theme_info["name"]
    all_items = []
    try:
        log("[1] 百度热榜...")
        r = requests.get("https://top.baidu.com/api/board/getBoard?boardId=realtime",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        for item in r.json().get("data", {}).get("content", [])[:30]:
            t = item.get("query", "")
            all_items.append({"title": t, "source": "百度", "score": score_item(t, theme_keywords)})
    except Exception as e:
        log(f"[1] 百度失败: {e}")
    try:
        log("[1] 微博热榜...")
        r = requests.get("https://weibo.com/ajax/side/hotSearch",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        for item in r.json().get("data", {}).get("realtime", [])[:30]:
            t = item.get("word", "")
            all_items.append({"title": t, "source": "微博", "score": score_item(t, theme_keywords)})
    except Exception as e:
        log(f"[1] 微博失败: {e}")
    try:
        log("[1] 头条热榜...")
        r = requests.get("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        for item in r.json().get("data", [])[:30]:
            t = item.get("Title", "")
            all_items.append({"title": t, "source": "头条", "score": score_item(t, theme_keywords)})
    except Exception as e:
        log(f"[1] 头条失败: {e}")
    relevant = [i for i in all_items if i["score"] > 0]
    relevant.sort(key=lambda x: x["score"], reverse=True)
    top5 = relevant[:5]
    if len(top5) < 3:
        log("[1] 素材不足，生成主题话题...")
        prompt = f"根据主题「{theme_info['theme']}」方向「{theme_info['direction']}」生成3个中老年公众号话题，每行一个："
        result = call_deepseek(prompt, "你是一个专业的内容策划师", 0.8, 500)
        if result:
            lines = [l.strip() for l in result.split("\n") if l.strip() and len(l.strip()) > 5]
            for item in lines[:3]:
                top5.append({"title": item, "source": f"{theme_name}推荐", "score": 5})
    with open(f"{DATA_DIR}/candidates.json", "w", encoding="utf-8") as f:
        json.dump({"items": top5, "weekday": weekday, "theme": theme_info}, f, ensure_ascii=False)
    log(f"[1] 采集完成: {len(top5)}条 ({theme_name})")
    return top5

def truncate_title_smart(title, max_bytes=60):
    """智能截断标题：优先在标点/空格处截断，避免中间断开"""
    if len(title.encode("utf-8")) <= max_bytes:
        return title
    
    # 标点符号优先断开点
    break_chars = ["，", "。", "！", "？", "、", "：", "；", " ", "｜", "|", "——", "…"]
    
    result = title
    while len(result.encode("utf-8")) > max_bytes and result:
        # 从后往前找断开点
        found_break = False
        for i in range(len(result) - 1, 0, -1):
            if result[i] in break_chars:
                result = result[:i]
                found_break = True
                break
        
        if not found_break:
            result = result[:-1]
    
    return result if result else title[:20]  # 保底

def node2_title():
    """生成标题：要求 15-22 字（45-66 字节），确保完整可读"""
    weekday, theme_info = get_weekday_theme()
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            data = json.load(f)
            items = data.get("items", [])
    except:
        items = [{"title": "健康养生"}]
    hot_topics = "\n".join([f"- {i['title']}" for i in items])
    theme_ctx = f"\n\n今日主题「{theme_info.get('name','')}」：{theme_info.get('theme','')}\n方向：{theme_info.get('direction','')}"
    
    # 生成标题提示词：明确字数限制
    prompt = f"""## 热榜话题
{hot_topics}
{theme_ctx}

## 标题生成要求
生成 5 个微信公众号爆款标题候选，然后选择最优的一个作为最终标题。

### 字数要求（重要）
- 标题字数：15-22 个汉字
- 字节限制：标题编码后不超过 60 字节（微信草稿箱限制 64 字节，留 4 字节余量）
- 标题必须完整、可读、有吸引力

### 标题风格
- 用数字、疑问、对比制造好奇
- 直接命中目标读者痛点
- 避免标题党，内容要能兑现承诺

## 输出格式
候选标题（5个）：
1. 15-22字标题
2. 15-22字标题
3. 15-22字标题
4. 15-22字标题
5. 15-22字标题

【最终标题】：选择最好的一个标题（15-22字）
"""
    log("[2] 生成标题（15-22字）...")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, 0.8, 800)
    
    final_title = None
    if result:
        for line in result.split("\n"):
            if "最终标题" in line:
                # 提取标题：找冒号或【】分隔
                raw = line.split("】")[-1].strip()  # 去掉【最终标题】前缀
                # 处理 "【最终标题】:xxx" 或 "【最终标题】：xxx" 或 "【最终标题】 xxx" 三种情况
                if "：" in raw:
                    t = raw.split("：", 1)[-1].strip()
                elif ":" in raw:
                    t = raw.split(":", 1)[-1].strip()
                else:
                    t = raw.strip()
                t = t.lstrip("：").lstrip(":").strip()  # 兜底：去掉可能残留的冒号和空格
                if t:
                    # 检查字节数
                    byte_len = len(t.encode("utf-8"))
                    char_len = len(t)
                    log(f"[2] 提取标题: '{t}' ({char_len}字, {byte_len}B)")
                    if byte_len <= 60 and 10 <= char_len <= 25:
                        final_title = t
                        break
                    elif byte_len > 60:
                        log(f"[2] 标题超长({byte_len}B)，智能截断...")
                        final_title = truncate_title_smart(t, 60)
                        break
    
    # 如果没拿到合适标题，用默认值
    if not final_title:
        fallback = items[0]["title"] if items else "健康养生小贴士"
        final_title = truncate_title_smart(fallback, 60)
        log(f"[2] 使用默认标题: {final_title}")
    
    with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
        json.dump({"title": final_title, "theme": theme_info, "weekday": weekday}, f, ensure_ascii=False)
    log(f"[2] 最终标题: '{final_title}' ({len(final_title)}字, {len(final_title.encode('utf-8'))}B)")
    return final_title

def node3_outline():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title_data = json.load(f)
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            cand_data = json.load(f)
        title = title_data["title"]
        source = cand_data.get("items", [{}])[0].get("source", "网络")
        theme_info = title_data.get("theme", {})
    except:
        title, source, theme_info = "健康养生", "网络", {}
    theme_ctx = f"\n\n今日主题「{theme_info.get('name','')}」：{theme_info.get('theme','')}"
    prompt = f"## 标题：{title}\n## 来源：{source}热榜{theme_ctx}\n\n输出【目标读者】【核心金句】【文章结构】【小标题】"
    log("[3] 生成大纲...")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, 0.7)
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump({"outline": result or "基础大纲", "title": title, "theme": theme_info}, f, ensure_ascii=False)
    log("[3] 大纲完成")
    return result

def node4_article():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title_data = json.load(f)
        with open(f"{DATA_DIR}/outline.json", encoding="utf-8") as f:
            outline_data = json.load(f)
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            cand_data = json.load(f)
        title = title_data["title"]
        outline = outline_data.get("outline", "")
        source = cand_data.get("items", [{}])[0].get("source", "网络")
        weekday = title_data.get("weekday", beijing_now().weekday())
        hist = read_articles(weekday, limit=4)
        hist_prompt = f"\n\n参考：\n{hist}\n" if hist else ""
    except:
        title, outline, source = "健康养生", "", "网络"
        hist_prompt = ""
    log("[4] 生成正文(Markdown格式)...")
    result = call_deepseek(THREE_HOOKS_ARTICLE_PROMPT.format(title=title, outline=outline[:2000] or "基础大纲") + hist_prompt,
                           THREE_HOOKS_SYSTEM, 0.8, 3000)
    article = result or f"【{title}】这是一篇健康养生文章。\n\n#健康 #养生"
    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({"title": title, "article": article, "source": source}, f, ensure_ascii=False)
    log(f"[4] 正文: {len(article)}字")
    return article

def node5_summary_and_cover():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title_data = json.load(f)
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article_data = json.load(f)
        title = title_data["title"]
        article = article_data["article"]
    except:
        title, article = "健康养生", "内容"
    log("[5] 生成摘要...")
    summary = call_deepseek(SUMMARY_PROMPT.format(title=title, article=article[:2000]),
                             "专业运营专家", 0.6, 300) or f"{title}，科学养生方法。"
    log("[5] 生成封面提示词...")
    cover_prompt = call_deepseek(COVER_PROMPT.format(title=title, article_summary=summary),
                                  "AI绘画工程师", 0.8, 500) or "A healthy lifestyle scene, 16:9, high quality."
    cover_url = generate_cover_image(cover_prompt)
    if not cover_url:
        log("[5] 通义万相失败，使用降级封面")
        weekday, theme_info = get_weekday_theme()
        cover_url = generate_fallback_cover(theme_info)
    with open(f"{DATA_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cover_prompt": cover_prompt, "cover_url": cover_url}, f, ensure_ascii=False)
    log(f"[5] 摘要({len(summary)}字) + 封面")
    return summary, cover_prompt, cover_url
def node6_send():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title_data = json.load(f)
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article_data = json.load(f)
        with open(f"{DATA_DIR}/summary.json", encoding="utf-8") as f:
            summary_data = json.load(f)
        title = title_data["title"]
        theme_info = title_data.get("theme", {})
        weekday = title_data.get("weekday", 0)
        article = article_data.get("article", "")
        source = article_data.get("source", "网络")
        summary = summary_data.get("summary", "")
        cover_prompt = summary_data.get("cover_prompt", "")
        cover_url = summary_data.get("cover_url", "")
    except Exception as e:
        log(f"[6] 读取数据失败: {e}")
        title, article, source, summary, cover_url, cover_prompt, theme_info, weekday = "健康养生文章", "内容", "网络", "", "", "", {}, 0

    # 推送到飞书文档
    feishu_url = push_to_feishu(title, article_data, summary, weekday, theme_info)
    
    # Server酱推送（用 Markdown 格式）
    feishu_line = f"📚 飞书文档：{feishu_url}\n" if feishu_url else ""
    serverchan_content = f"""📝 新文章：

📅 {WEEKDAY_NAMES[weekday]} · {theme_info.get('name', '健康养生')}
📌 今日主题：{theme_info.get('theme', '')}
📊 素材来源：{source}
{feishu_line}━━━━━━━━━━━━━━━

🏷️ 标题：{title}

📋 摘要：{summary}

━━━━━━━━━━━━━━━

📄 正文：
{article}

━━━━━━━━━━━━━━━

🎨 封面图：{cover_url or '生成失败'}

💡 封面提示词：{cover_prompt}

━━━━━━━━━━━━━━━
👆 以上是今日生成的文章内容"""
    result = send_to_wechat(f"📝 新文章：{title}", serverchan_content)

    # === 微信草稿箱推送（用 HTML 格式） ===
    draft_ok = False
    if cover_url:
        log("[6] 推送至微信草稿箱...")
        log(f"[6] 使用主题样式: {WEEKDAY_NAMES[weekday]} · {theme_info.get('name', '')}")
        
        # === 拼装完整文章（文首固定标识 + 正文 + 文末预告 + 引导关注） ===
        banner = WEEKLY_BANNERS.get(weekday, {})
        next_wk = (weekday + 1) % 7
        next_banner = WEEKLY_BANNERS.get(next_wk, {})
        
        # 文首固定标识（Markdown格式，转为HTML后样式由markdown_to_html处理）
        banner_md = f"{banner.get('icon', '')} **{WEEKDAY_NAMES[weekday]} · {theme_info.get('name', '')}**「{banner.get('column', '')}」{banner.get('slogan', '')}"
        
        # 文末预告（Markdown格式）
        preview_md = f"📅 明天 **「{next_banner.get('column', '')}」**：{next_banner.get('icon', '')} {WEEKDAY_NAMES[next_wk]} · {next_banner.get('slogan', '')}"
        
        # 引导关注（Markdown引用格式）
        about_md = "> " + ABOUT_TEXT.replace("\n\n", "\n> \n> ")
        
        # 完整Markdown文章
        article_full_md = f"{banner_md}\n\n{article}\n\n---\n\n{preview_md}\n\n{about_md}"
        
        # Markdown → HTML（应用当天主题样式）
        article_html = markdown_to_html(article_full_md, weekday)
        
        digest = (summary[:54] + "…") if len(summary) > 54 else summary
        author = theme_info.get("name", "健康养生")
        draft_ok = push_article_to_draft(title, author, digest, article_html, cover_url, weekday)
        if draft_ok:
            log("[6] 草稿箱推送成功！")
            send_to_wechat("✅ 草稿箱推送成功",
                           f"📝 《{title}》已推送至微信公众号草稿箱\n📅 主题：{WEEKDAY_NAMES[weekday]} · {theme_info.get('name', '')}\n🎨 封面：{cover_url}\n\n请登录公众号后台 → 内容与互动 → 草稿箱 查看并发布。")
        else:
            log("[6] 草稿箱推送失败（Server酱已成功）")

    if result.get("code") == 0:
        log("[6] Server酱发送成功！")
        return {"status": "success", "cover_url": cover_url, "draft": draft_ok}
    return {"status": "failed", "error": result}

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "version": "v3.0",
        "message": "内容流水线（七天主题样式系统）",
        "endpoints": {
            "GET /": "健康检查",
            "GET /trigger?force=1": "手动触发完整流程"
        }
    })

@app.route("/trigger")
def trigger():
    force = request.args.get("force", "0") == "1"
    today = beijing_now().strftime('%Y%m%d')
    lock_file = f"{DATA_DIR}/executed_{today}.lock"

    # ⏱️ 5分钟冷却锁，防止频繁触发
    recent_lock = f"{DATA_DIR}/recent_trigger.lock"
    if os.path.exists(recent_lock):
        age = time.time() - os.path.getmtime(recent_lock)
        if age < 300 and not force:
            log(f"⏳ 触发太频繁，距上次 {int(age)}s，请{int(300-age)}s后再试")
            return jsonify({"success": False, "error": f"冷却中，请{int(300-age)}s后再试（已过{int(age)}s）"}), 429

    if os.path.exists(lock_file) and not force:
        log("⏭️ 今日已执行，跳过")
        return jsonify({"success": True, "result": {"status": "skipped"}})
    log("=" * 50)
    log("🚀 流水线启动")
    log("=" * 50)
    try:
        # ⏱️ 更新冷却锁
        with open(recent_lock, 'w') as f:
            f.write(datetime.now().isoformat())

        node1_collector()
        node2_title()
        node3_outline()
        node4_article()
        node5_summary_and_cover()
        result = node6_send()
        with open(lock_file, 'w') as f:
            f.write(datetime.now().isoformat())
        log("=" * 50)
        log("🏁 流水线完成")
        log("=" * 50)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        log(f"错误: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
