from flask import Flask, jsonify, request
import os, json, requests, base64, hashlib, hmac, time, urllib.parse, io
from datetime import datetime, timezone, timedelta
from PIL import Image

BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    return datetime.now(BEIJING_TZ)

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))
DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "SCT333499TpvZQWzbvJcMfDxo7BmL8MsrV")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6e2b402410694b50af206daee4f017bc")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
WANXIANG_API_KEY = os.environ.get("WANXIANG_API_KEY", "sk-de7984bb01c84a2bb136167006864fe2")
WX_APPID = os.environ.get("WX_APPID", "")
WX_APPSECRET = os.environ.get("WX_APPSECRET", "")

WEEKLY_THEMES = {
    0: {"name": "情感心理", "theme": "面对空巢与孤独，老人的情感需求正在被看见",
        "keywords": ["孤独", "空巢", "独居", "陪伴", "代际", "子女", "父母", "养老", "思念", "老年", "退休", "情感", "亲情", "家庭", "寂寞"],
        "direction": "如何面对独居/空巢/孤独感、代际沟通（如何与子女相处）"},
    1: {"name": "养生生活", "theme": "中式轻养生，正在成为最易传播的日常内容",
        "keywords": ["养生", "中医", "食疗", "药食同源", "食谱", "饮食", "进补", "体质", "节气", "四季", "春季", "养肝", "健脾", "抗炎", "营养", "早餐", "晚餐"],
        "direction": "四季顺时养生（如春季防风护肝）、药食同源食谱、一日三餐怎么吃"},
    2: {"name": "慢病管理", "theme": "三高、心血管等慢性病，正在成为最刚需的科普",
        "keywords": ["高血压", "高血糖", "高血脂", "三高", "糖尿病", "心梗", "中风", "脑梗", "心血管", "心脏病", "胆固醇", "血脂", "血糖", "血压", "慢性病", "服药", "用药"],
        "direction": "高血压/糖尿病怎么吃、用药常识（千万别犯的错）、慢病的日常监测与护理"},
    3: {"name": "情绪养生", "theme": "坏情绪比高血压更伤身，老年人的心理问题不容忽视",
        "keywords": ["抑郁", "焦虑", "失眠", "情绪", "心理健康", "孤独", "悲观", "心态", "老年痴呆", "阿尔茨海默", "记忆", "认知", "精神", "心理", "情绪管理"],
        "direction": "焦虑/抑郁的识别与应对、情绪急救方法、孤独感的排解、如何保持乐观心态"},
    4: {"name": "生活品质", "theme": "银发族的消费升级，如何把钱花在刀刃上",
        "keywords": ["消费", "购物", "保健品", "营养品", "体检", "保险", "理财", "退休", "养老金", "省钱", "购物车", "礼物", "适老化", "产品", "测评", "避坑"],
        "direction": "健康消费避坑指南、适老化产品测评、如何科学选购保健品/家用医疗器械"},
    5: {"name": "科技健康", "theme": "AI与智能设备，正在改变老年人的健康管理方式",
        "keywords": ["手机", "APP", "智能", "科技", "AI", "人工智能", "健康码", "挂号", "预约", "视频", "微信", "网络", "智能手表", "血压计", "血糖仪", "健康监测"],
        "direction": "AI健康助手怎么用、智能监测设备推荐、科技如何帮老人老有所依"},
    6: {"name": "科普急救", "theme": "关键时刻能救命的硬知识，是最能打动人心的内容",
        "keywords": ["急救", "心梗", "中风", "脑梗", "猝死", "心肺复苏", "急救常识", "家庭药箱", "常备药", "心脏病", "胸痛", "呼吸困难", "跌倒", "烫伤", "噎住", "异物"],
        "direction": "心脑血管疾病预防与急救、中风/心梗的识别与应对、家庭常备药品清单、用药安全指南"}
}

KEYWORDS = ["健康", "养生", "中医", "运动", "睡眠", "心理", "情感", "饮食", "减肥", "健身", "血压", "血糖", "心脏", "癌症", "疫苗", "医院", "医生", "药品", "保健", "体检", "养老", "老年", "中年", "退休", "家庭", "婚姻", "孩子"]

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

def send_to_wechat(title, content):
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        resp = requests.post(url, data={"title": title, "desp": content}, timeout=10)
        result = resp.json()
        log(f"[推送] 发送结果: {result}")
        return result
    except Exception as e:
        log(f"[推送] 发送失败: {e}")
        return {"code": -1, "msg": str(e)}

def call_deepseek(prompt, system_prompt="你是一个有用的助手", temperature=0.7, max_tokens=2500):
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens}
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=180)
        result = resp.json()
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        log(f"[DeepSeek] API错误: {result}")
        return None
    except Exception as e:
        log(f"[DeepSeek] 调用失败: {e}")
        return None

def generate_cover_image(prompt):
    try:
        log(f"[封面] 生成封面图...")
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {WANXIANG_API_KEY}", "X-DashScope-Async": "enable"}
        payload = {"model": "wanx-v1", "input": {"prompt": prompt}, "parameters": {"style": "<auto>", "size": "1280*720", "n": 1}}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        result = resp.json()
        log(f"[封面] 任务创建: {result}")
        if "output" in result and "task_id" in result["output"]:
            task_id = result["output"]["task_id"]
            for i in range(30):
                time.sleep(3)
                status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
                status_resp = requests.get(status_url, headers={"Authorization": f"Bearer {WANXIANG_API_KEY}"})
                status_result = status_resp.json()
                task_status = status_result.get("output", {}).get("task_status", "")
                log(f"[封面] 状态: {task_status}")
                if task_status == "SUCCEEDED":
                    results = status_result.get("output", {}).get("results", [])
                    if results:
                        image_url = results[0].get("url", "")
                        log(f"[封面] ✅ 生成成功: {image_url}")
                        return image_url
                elif task_status == "FAILED":
                    log(f"[封面] 生成失败: {status_result}")
                    return None
            log("[封面] 超时")
            return None
        log(f"[封面] 创建失败: {result}")
        return None
    except Exception as e:
        log(f"[封面] 异常: {e}")
        return None

def get_access_token():
    if not WX_APPID or not WX_APPSECRET:
        log("[微信] 缺少 WX_APPID 或 WX_APPSECRET")
        return None
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": WX_APPID, "secret": WX_APPSECRET}
    resp = requests.get(url, params=params, timeout=10)
    result = resp.json()
    if "access_token" in result:
        log(f"[微信] Access Token: {result['access_token'][:20]}...")
        return result["access_token"]
    log(f"[微信] Access Token 获取失败: {result}")
    return None

def upload_cover_for_draft(access_token, image_url):
    log(f"[微信] 下载封面图: {image_url}")
    img_resp = requests.get(image_url, timeout=30)
    if img_resp.status_code != 200:
        log(f"[微信] 图片下载失败: HTTP {img_resp.status_code}")
        return None
    original_bytes = img_resp.content
    log(f"[微信] 原始: {len(original_bytes)/1024:.1f} KB")
    try:
        img = Image.open(io.BytesIO(original_bytes))
        log(f"[微信] 尺寸: {img.width}x{img.height}, 模式: {img.mode}")
    except Exception as e:
        log(f"[微信] Pillow 打开失败: {e}")
        return None
    if img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    tgt_w, tgt_h = 900, 506
    if img.width > tgt_w:
        ratio = tgt_w / img.width
        img = img.resize((tgt_w, int(img.height * ratio)), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85, optimize=True)
    compressed = output.getvalue()
    log(f"[微信] 压缩后: {len(compressed)/1024:.1f} KB")
    upload_url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    files = {"media": ("cover.jpg", compressed, "image/jpeg")}
    data = {"access_token": access_token, "type": "image"}
    upload_resp = requests.post(upload_url, params=data, files=files, timeout=30)
    upload_result = upload_resp.json()
    log(f"[微信] 上传结果: {upload_result}")
    if "media_id" in upload_result:
        media_id = upload_result["media_id"]
        thumb_url = upload_result.get("url", "")
        log(f"[微信] ✅ media_id: {media_id}")
        return {"media_id": media_id, "url": thumb_url}
    log(f"[微信] ❌ 上传失败: {upload_result}")
    return None

def create_draft(access_token, title, author, digest, content_html, media_id, thumb_url=""):
    log(f"[微信] 创建草稿箱文章...")
    title_utf8 = len(title.encode("utf-8"))
    log(f"[微信] 标题: '{title}' ({title_utf8}B)")
    if title_utf8 > 64:
        title = title.encode("utf-8")[:64].decode("utf-8", errors="ignore")
        log(f"[微信] ⚠️ 截断: '{title}'")
    payload = {"articles": [{"title": title, "author": author, "digest": digest, "content": content_html,
                              "content_source_url": "", "thumb_media_id": media_id, "thumb_url": thumb_url}]}
    url = "https://api.weixin.qq.com/cgi-bin/draft/add"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    json_body = json.dumps(payload, ensure_ascii=False)
    resp = requests.post(url, params={"access_token": access_token}, data=json_body.encode("utf-8"),
                         headers=headers, timeout=15)
    result = resp.json()
    log(f"[微信] 创建结果: {result}")
    if result.get("errcode") == 0 or "media_id" in result:
        log("[微信] ✅ 草稿创建成功！")
        return True
    log(f"[微信] ❌ 草稿创建失败: {result}")
    return False

def push_article_to_draft(title, author, digest, content_html, cover_url):
    if not WX_APPID or not WX_APPSECRET:
        log("[草稿] 缺少微信公众号凭证，跳过")
        return False
    access_token = get_access_token()
    if not access_token:
        return False
    media_result = upload_cover_for_draft(access_token, cover_url)
    if not media_result:
        return False
    success = create_draft(access_token, title, author, digest, content_html,
                           media_result["media_id"], media_result.get("url", ""))
    return success

THREE_HOOKS_SYSTEM = '你是一位顶级微信公众号爆款文章写作大师，擅长用"三把钩子"写作法创作高转发、高点赞的爆款文章。'

THREE_HOOKS_ARTICLE_PROMPT = """## 任务
根据以下大纲，写一篇微信公众号爆款文章。

## 标题
{title}

## 大纲
{outline}

## 写作要求
1. 字数：1200-1500字，结尾附5个话题标签 #话题标签
2. 去结构化：口语化，每段落≤5行，不用1、2、3排序
3. 去AI味：不用首先/其次/再次/最后/总之/综上所述，不用破折号
4. 内容原创：严禁抄袭，有立场有情绪，不要中立
5. 排版：每段落≤5行，可用emoji分段

### 三把钩子写作法
**第一把钩子**：开头一秒钩住读者——目标读者画像+扎心问题+痛点场景+好处承诺
**第二把钩子**：中间建立信任——核心观点+真实例子+底层逻辑（"其实……"开头）+对比反差
**第三把钩子**：结尾让人行动/收藏/转发——可操作步骤+亲身经历+金句收尾+互动提问

### 自检清单
- 开头命中痛点？例子有名字/细节/画面？解释"为什么"？读者知道第一步？
- 故事出现？结尾引发收藏/转发/留言？

直接输出正文，文末加5个话题标签。"""

SUMMARY_PROMPT = """## 任务
根据以下文章，生成80-90字的摘要。

## 标题
{title}

## 正文
{article}

要求：简洁有力，吸引点击。直接输出摘要。"""

COVER_PROMPT = """## 任务
根据以下文章，生成AI绘画提示词。

## 标题
{title}
## 主题摘要
{article_summary}

## 要求
- 主体：人物 / 建筑 / 静物 / 风景
- 场景：时间（黄昏/夜晚）、地点（街头/山间/室内）
- 光线：逆光、侧光、柔光、霓虹灯、窗边自然光
- 风格：胶片感、日系、赛博朋克、纪实、商业人像等
- 构图：广角、特写、中景、俯拍、仰拍等
- 比例：16:9
- 虚实相生：实（人物/神态/行为/环境）+ 虚（光影/色彩/情绪/风格）

直接输出中文提示词。"""

def get_weekday_theme():
    weekday = beijing_now().weekday()
    theme_info = WEEKLY_THEMES.get(weekday, WEEKLY_THEMES[0])
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
    log(f"[1] ✅ 采集完成: {len(top5)}条 ({theme_name})")
    return top5

def node2_title():
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            data = json.load(f)
            items, theme_info = data["items"], data.get("theme", {})
        hot_topics = "\n".join([f"- {i['title']}" for i in items])
    except:
        hot_topics, items, theme_info = "健康养生", [{"title": "健康养生"}], {}
    theme_ctx = f"\n\n今日主题「{theme_info.get('name','')}」：{theme_info.get('theme','')}\n方向：{theme_info.get('direction','')}"
    prompt = f"## 热榜话题\n{hot_topics}\n{theme_ctx}\n\n生成5个微信公众号爆款标题，选最优。最终标题不超过30字。\n\n候选标题（5个）：\n1. xxx\n2. xxx\n3. xxx\n4. xxx\n5. xxx\n\n【最终标题】：xxx"
    log("[2] 生成标题...")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, 0.8)
    final_title = None
    if result:
        for line in result.split("\n"):
            if "最终标题" in line:
                t = line.split("】")[-1].strip() or line.split("：")[-1].strip()
                if t and len(t) <= 50:
                    final_title = t
                    break
    if not final_title:
        final_title = items[0]["title"] if items else "健康养生"
    while len(final_title.encode("utf-8")) > 60:
        final_title = final_title[:-1]
    with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
        json.dump({"title": final_title, "theme": theme_info}, f, ensure_ascii=False)
    log(f"[2] ✅ 标题: {final_title}")
    return final_title

def node3_outline():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            data = json.load(f)
            source = data["items"][0].get("source", "网络")
            theme_info = data.get("theme", {})
    except:
        title, source, theme_info = "健康养生", "网络", {}
    theme_ctx = f"\n\n今日主题「{theme_info.get('name','')}」：{theme_info.get('theme','')}"
    prompt = f"## 标题：{title}\n## 来源：{source}热榜{theme_ctx}\n\n输出【目标读者】【核心金句】【文章结构】【小标题】"
    log("[3] 生成大纲...")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, 0.7)
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump({"outline": result or "基础大纲", "title": title, "theme": theme_info}, f, ensure_ascii=False)
    log("[3] ✅ 大纲完成")
    return result

def node4_article():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/outline.json", encoding="utf-8") as f:
            outline = json.load(f).get("outline", "")
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            source = json.load(f)["items"][0].get("source", "网络")
    except:
        title, outline, source = "健康养生", "", "网络"
    log("[4] 生成正文...")
    result = call_deepseek(THREE_HOOKS_ARTICLE_PROMPT.format(title=title, outline=outline[:2000] or "基础大纲"),
                           THREE_HOOKS_SYSTEM, 0.8, 3000)
    article = result or f"【{title}】这是一篇健康养生文章。\n\n#健康 #养生"
    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({"title": title, "article": article, "source": source}, f, ensure_ascii=False)
    log(f"[4] ✅ 正文: {len(article)}字")
    return article

def node5_summary_and_cover():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article = json.load(f)["article"]
    except:
        title, article = "健康养生", "内容"
    log("[5] 生成摘要...")
    summary = call_deepseek(SUMMARY_PROMPT.format(title=title, article=article[:2000]),
                             "专业运营专家", 0.6, 300) or f"{title}，科学养生方法。"
    log("[5] 生成封面提示词...")
    cover_prompt = call_deepseek(COVER_PROMPT.format(title=title, article_summary=summary),
                                  "AI绘画工程师", 0.8, 500) or "A healthy lifestyle scene, 16:9, high quality."
    cover_url = generate_cover_image(cover_prompt)
    with open(f"{DATA_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cover_prompt": cover_prompt, "cover_url": cover_url}, f, ensure_ascii=False)
    log(f"[5] ✅ 摘要({len(summary)}字) + 封面")
    return summary, cover_prompt, cover_url

def node6_send():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
            theme_info = json.load(f).get("theme", {})
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article = json.load(f).get("article", "")
            source = json.load(f).get("source", "网络")
        with open(f"{DATA_DIR}/summary.json", encoding="utf-8") as f:
            data = json.load(f)
            summary, cover_prompt, cover_url = data.get("summary", ""), data.get("cover_prompt", ""), data.get("cover_url", "")
    except Exception as e:
        log(f"[6] 读取数据失败: {e}")
        title, article, source, summary, cover_url, cover_prompt, theme_info = "健康养生文章", "内容", "网络", "", "", "", {}
    weekday, _ = get_weekday_theme()
    theme_tag = f"📌 **今日主题：** {theme_info.get('name', '健康养生')} · {theme_info.get('theme', '')}"

    # === Server酱推送（新格式）===
    serverchan_content = f"""📝 新文章：

📅 周{WEEKDAY_NAMES[weekday]} · {theme_info.get('name', '健康养生')}
📌 今日主题：{theme_info.get('theme', '')}
📊 素材来源：{source}

━━━━━━━━━━━━━━━

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

    # === 微信草稿箱推送 ===
    draft_ok = False
    if cover_url:
        log("[6] 推送至微信草稿箱...")
        digest = summary[:54] + "…" if len(summary) > 54 else summary
        author = theme_info.get("name", "健康养生")
        draft_ok = push_article_to_draft(title, author, digest, article, cover_url)
        if draft_ok:
            log("[6] ✅ 草稿箱推送成功！")
            send_to_wechat("✅ 草稿箱推送成功",
                           f"📝 《{title}》已推送至微信公众号草稿箱\n🎨 封面：{cover_url}\n\n请登录公众号后台 → 内容与互动 → 草稿箱 查看并发布。")
        else:
            log("[6] ⚠️ 草稿箱推送失败（Server酱已成功）")

    if result.get("code") == 0:
        log("[6] ✅ Server酱发送成功！")
        return {"status": "success", "cover_url": cover_url, "draft": draft_ok}
    return {"status": "failed", "error": result}

@app.route("/")
def index():
    return "✅ 内容流水线 v2.0（Server酱详细格式 + 微信草稿箱）<br>• GET /trigger → 触发完整流水线<br>• GET /test_draft → 测试草稿箱<br>• GET /test_status → 检查配置"

@app.route("/test_status")
def test_status():
    return jsonify({
        "WX_APPID": "✅" if WX_APPID else "❌ 未配置",
        "WX_APPSECRET": "✅" if WX_APPSECRET else "❌ 未配置",
        "SERVERCHAN_KEY": "✅" if SERVERCHAN_KEY else "❌",
        "WANXIANG_API_KEY": "✅" if WANXIANG_API_KEY else "❌",
        "DEEPSEEK_API_KEY": "✅" if DEEPSEEK_API_KEY else "❌",
    })

@app.route("/test_draft")
def test_draft():
    log("=" * 50)
    log("🧪 草稿箱测试")
    log("=" * 50)
    cover_url = generate_cover_image(
        "An elderly Chinese woman sitting by the window, looking out at a quiet neighborhood, warm afternoon sunlight, gentle and peaceful atmosphere, realistic photography style, 16:9"
    )
    if not cover_url:
        return jsonify({"success": False, "error": "封面图生成失败"}), 500
    success = push_article_to_draft(
        "子女不在身边，老人如何告别孤独感？",
        "健康养生",
        "子女不在身边，空巢老人的孤独感如何化解？这三个方法值得尝试。",
        '<p>李阿姨今年68岁，退休前是小学老师。老伴三年前走了，儿子在上海工作，一年回来两三次。</p><p>她说，最难熬的不是夜里醒来的那两个小时，而是白天。手机里儿子的照片看了又看，想打电话又怕打扰他工作。</p><p>这是很多空巢老人的真实写照。孤独感对老年人的伤害，比我们想象的大得多。</p><p>那怎么办？</p><p>第一，给自己找个"寄托"。养花、养鸟、养猫狗都行，重要的是有个活物等着你回家。</p><p>第二，主动走出去，别等别人来找你。小区里的广场舞队、棋牌室、社区老年大学，都是好去处。</p><p>第三，学会用手机和儿女"见面"。微信视频比打电话强多了，能看见脸的距离感，比听到声音的孤独感要小很多。</p><p>老有所依，不是物质上的依靠，是心里的那份牵挂。</p>',
        cover_url
    )
    if success:
        send_to_wechat("✅ 草稿箱推送成功", f"📝 《子女不在身边，老人如何告别孤独感？》已推送\n🎨 封面：{cover_url}")
        return jsonify({"success": True, "cover_url": cover_url})
    return jsonify({"success": False, "error": "草稿箱推送失败"}), 500

@app.route("/trigger")
def trigger():
    force = request.args.get("force", "0") == "1"
    today = beijing_now().strftime('%Y%m%d')
    lock_file = f"{DATA_DIR}/executed_{today}.lock"
    if os.path.exists(lock_file) and not force:
        log("⏭️ 今日已执行，跳过")
        return jsonify({"success": True, "result": {"status": "skipped"}})
    log("=" * 50)
    log("🚀 流水线启动")
    log("=" * 50)
    try:
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
