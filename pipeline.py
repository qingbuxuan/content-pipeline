# -*- coding: utf-8 -*-
"""内容流水线：节点函数 + 飞书记录 + Flask 路由"""
from config import *
from html_converter import *
from utils import *
from wechat import *
from prompts import *

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
                # 提取标题
                t = line.split("】")[-1].strip() or line.split("：")[-1].strip()
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


# 飞书多维表格配置
FEISHU_BITABLE_TOKEN = "THaEbbUfWak0d2sVpCbcXW4Dnfe"
FEISHU_ARTICLES_TABLE_ID = None  # 运行时自动检测/创建

def get_feishu_token():
    """获取飞书 access_token"""
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if not app_id or not app_secret:
        log(f"[飞书] 环境变量缺失: app_id={'有' if app_id else '无'}, app_secret={'有' if app_secret else '无'}")
        return None
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        log(f"[飞书] Token获取失败 code={data.get('code')}: {data.get('msg', data)}")
        return None
    if "tenant_access_token" not in data:
        log(f"[飞书] Token响应格式异常: {str(data)[:200]}")
        return None
    return data["tenant_access_token"]

def ensure_articles_table(token):
    """确保公众号文章记录表存在，创建必要的字段，返回 table_id"""
    global FEISHU_ARTICLES_TABLE_ID
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 列出现有表
    list_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables"
    list_resp = requests.get(list_url, headers=headers, timeout=10)
    list_data = list_resp.json()
    
    if list_data.get("code") != 0:
        log(f"[飞书] 获取表格列表失败: {list_data}")
        return None
    
    table_id = None
    for table in list_data.get("data", {}).get("items", []):
        if table.get("name") == "公众号文章记录":
            table_id = table.get("table_id")
            FEISHU_ARTICLES_TABLE_ID = table_id
            log(f"[飞书] 找到公众号文章记录表: {table_id}")
            break
    
    # 2. 不存在则创建
    if not table_id:
        log("[飞书] 创建公众号文章记录表...")
        create_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables"
        create_resp = requests.post(create_url, headers=headers, json={"table": {"name": "公众号文章记录"}}, timeout=10)
        create_data = create_resp.json()
        
        if create_data.get("code") != 0:
            log(f"[飞书] 创建表失败: {create_data}")
            return None
        
        table_id = create_data["data"]["table_id"]
        FEISHU_ARTICLES_TABLE_ID = table_id
        log(f"[飞书] 表创建成功: {table_id}")
    
    # 3. 查询现有字段
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/fields"
    fields_resp = requests.get(fields_url, headers=headers, timeout=10)
    fields_data = fields_resp.json()
    existing_field_names = {f["field_name"] for f in fields_data.get("data", {}).get("items", [])}
    log(f"[飞书] 现有字段: {existing_field_names}")
    
    # 4. 定义需要创建的字段
    field_defs = [
        ("日期", 5, None),
        ("星期", 3, {"options": [{"name": n} for n in WEEKDAY_NAMES]}),
        ("主题", 3, {"options": [{"name": "情感心理"}, {"name": "养生生活"}, {"name": "慢病管理"}, {"name": "情绪养生"}, {"name": "生活品质"}, {"name": "科技健康"}, {"name": "科普急救"}]}),
        ("标题", 1, None),
        ("摘要", 1, None),
        ("飞书文档", 15, None),
        ("微信状态", 3, {"options": [{"name": "草稿"}, {"name": "已发布"}, {"name": "未发"}]}),
        ("封面图", 15, None),
        ("素材来源", 1, None),
    ]
    
    # 5. 创建缺失的字段
    for field_name, field_type, field_property in field_defs:
        if field_name in existing_field_names:
            log(f"[飞书] 字段已存在，跳过: {field_name}")
            continue
        
        field_payload = {"field_name": field_name, "type": field_type}
        if field_property:
            field_payload["property"] = field_property
        
        create_field_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/fields"
        create_resp = requests.post(create_field_url, headers=headers, json=field_payload, timeout=10)
        result = create_resp.json()
        
        if result.get("code") != 0:
            log(f"[飞书] 创建字段失败 [{field_name}]: {result}")
        else:
            log(f"[飞书] 字段创建成功: {field_name} (type={field_type})")
    
    # 6. 再次验证
    verify_resp = requests.get(fields_url, headers=headers, timeout=10)
    verify_data = verify_resp.json()
    final_fields = [f["field_name"] for f in verify_data.get("data", {}).get("items", [])]
    log(f"[飞书] 最终字段列表: {final_fields}")
    
    return table_id
    return table_id

def write_article_record(token, table_id, record_data):
    """写入公众号文章记录到多维表格（自动适配实际字段名）"""
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 查询实际字段名
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/fields"
    fields_resp = requests.get(fields_url, headers=headers, timeout=10)
    fields_data = fields_resp.json()

    if fields_data.get("code") != 0:
        log(f"[飞书] 查询字段失败: {fields_data}")
        return None

    actual_fields = {f["field_name"]: f for f in fields_data.get("data", {}).get("items", [])}
    log(f"[飞书] 实际字段: {list(actual_fields.keys())}")

    # 2. 字段名映射（中文名 -> 值）
    field_mapping = {
        "日期": record_data.get("date", 0) * 1000,
        "星期": record_data.get("weekday", ""),
        "主题": record_data.get("theme", ""),
        "标题": record_data.get("title", ""),
        "摘要": record_data.get("summary", ""),
        "飞书文档": {"link": record_data.get("doc_url", ""), "text": "打开文档"},
        "微信状态": "草稿",
        "封面图": {"link": record_data.get("cover_url", ""), "text": "封面"},
        "素材来源": record_data.get("source", "网络"),
    }

    # 3. 用实际字段名构造写入数据
    fields_to_write = {}
    for cn_name, value in field_mapping.items():
        matched_name = None
        if cn_name in actual_fields:
            matched_name = cn_name
        else:
            # 模糊匹配
            for fname in actual_fields:
                if cn_name in fname or fname in cn_name:
                    matched_name = fname
                    break
        if matched_name:
            fields_to_write[matched_name] = value
        else:
            log(f"[飞书] 跳过字段（未找到）: {cn_name}")

    # 4. 写入记录
    write_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/records"
    resp = requests.post(write_url, headers=headers, json={"fields": fields_to_write}, timeout=10)
    data = resp.json()

    if data.get("code") != 0:
        log(f"[飞书] 写入记录失败: {data}")
        return None

    log("[飞书] 记录写入成功")
    return data.get("data", {}).get("record", {}).get("record_id")


def push_to_feishu(title, article, summary, weekday, theme_info):
    """推送到飞书文档 + 多维表格"""
    try:
        # 读取环境变量
        app_id = os.environ.get("FEISHU_APP_ID", "")
        app_secret = os.environ.get("FEISHU_APP_SECRET", "")
        if not app_id or not app_secret:
            log("[飞书] 缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
            return None
        
        # 1. 获取 access_token
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        token_resp = requests.post(token_url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
        token_data = token_resp.json()
        access_token = token_data.get("tenant_access_token")
        if not access_token:
            log(f"[飞书] Token获取失败: {token_data}")
            return None
        
        # 2. 构造文档内容（飞书 JSON 格式）
        date_str = beijing_now().strftime("%Y-%m-%d")
        theme_name = theme_info.get("name", "健康养生")
        theme_day = WEEKDAY_NAMES[weekday]
        
        # 文档标题：2026-04-12 周一情感心理 - 老人孤独感如何化解
        doc_title = f"{date_str} {theme_day}{theme_name} - {title}"
        
        # 飞书文档块格式
        blocks = [
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📅 {date_str} {theme_day} · {theme_name}"}], "text_styles": {"bold": True}}},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📌 主题：{theme_info.get('theme', '')}"}]}},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📝 来源：{article.get('source', '网络')}"}]}},
            {"block_type": 1, "is_collapsible": False, "layout": "paragraph", "elements": []},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"🏷️ 标题：{title}"}], "text_styles": {"bold": True}}},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📋 摘要：{summary}"}]}},
            {"block_type": 1, "is_collapsible": False, "layout": "paragraph", "elements": []},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": "📄 正文："}], "text_styles": {"bold": True}}},
        ]
        
        # 正文分段（飞书每块有限制）
        article_lines = article.get("article", "").split("\n")
        for line in article_lines[:100]:  # 限制50行
            if line.strip():
                blocks.append({"block_type": 2, "text": {"elements": [{"type": "text_run", "text": line}]}})
        
        # 3. 创建文档
        create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        headers = {"Authorization": f"Bearer {access_token}"}
        create_resp = requests.post(create_url, headers=headers, json={"document_id": "", "title": doc_title}, timeout=10)
        create_data = create_resp.json()
        
        if create_data.get("code") != 0:
            log(f"[飞书] 创建文档失败: {create_data}")
            return None
        
        doc_token = create_data["data"]["document"]["token"]
        
        # 4. 写入内容块
        children_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
        children_resp = requests.post(children_url, headers=headers, json={"children": blocks, "index": -1}, timeout=30)
        children_data = children_resp.json()
        
        if children_data.get("code") != 0:
            log(f"[飞书] 写入内容失败: {children_data}")
            # 继续尝试写表
        else:
            log(f"[飞书] 文档内容写入成功")
        
        # 5. 生成分享链接
        share_url = f"https://feishu.cn/docx/{doc_token}"
        log(f"[飞书] 文档已创建: {share_url}")
        
        # 6. 写入多维表格
        log(f"[飞书] 开始写入多维表格...")
        table_id = ensure_articles_table(access_token)
        log(f"[飞书] 获取到表ID: {table_id}")
        if table_id:
            import time
            record_data = {
                "date": int(time.time()),
                "weekday": theme_day,
                "theme": theme_info.get("name", ""),
                "title": title,
                "summary": summary,
                "doc_url": share_url,
                "cover_url": article.get("cover_url", ""),
                "source": article.get("source", "网络"),
            }
            log(f"[飞书] 准备写入记录: {record_data}")
            record_id = write_article_record(access_token, table_id, record_data)
            log(f"[飞书] 记录写入结果: {record_id}")
        else:
            log(f"[飞书] 未获取到表ID，跳过写表")
        
        return share_url
        
    except Exception as e:
        import traceback
        log(f"[飞书] 推送异常: {e}")
        log(f"[飞书] 异常详情: {traceback.format_exc()}")
        return None


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
        
        # Markdown → HTML（应用当天主题样式）
        article_html = markdown_to_html(article, weekday)
        
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
