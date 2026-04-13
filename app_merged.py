from flask import Flask, jsonify, request
import os, json, requests, base64, hashlib, hmac, time, urllib.parse, io, re
from datetime import datetime, timezone, timedelta
from PIL import Image
import markdown

BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    return datetime.now(BEIJING_TZ)

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))
DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
WANXIANG_API_KEY = os.environ.get("WANXIANG_API_KEY", "")
WX_APPID = os.environ.get("WX_APPID", "")
WX_APPSECRET = os.environ.get("WX_APPSECRET", "")

# ========== 七天主题样式系统 ==========
# 每天一个主题，每个主题一套配色方案
STYLE_THEMES = {
    0: {  # 周一 · 情感心理 - 温暖粉红调
        "name": "情感心理",
        "theme": "面对空巢与孤独，老人的情感需求正在被看见",
        "keywords": ["孤独", "空巢", "独居", "陪伴", "代际", "子女", "父母", "养老", "思念", "老年", "退休", "情感", "亲情", "家庭", "寂寞"],
        "direction": "如何面对独居/空巢/孤独感、代际沟通（如何与子女相处）",
        "colors": {
            "primary": "#e91e63",      # 主色：粉红
            "heading": "#880e4f",      # 标题色：深玫红
            "text": "#5d4037",         # 正文色：暖棕
            "strong": "#c2185b",       # 重点色：玫红
            "strong_bg": "#fce4ec",    # 重点背景：浅粉
            "quote_border": "#f48fb1", # 引用边框：浅粉红
            "quote_bg": "#fce4ec",     # 引用背景：浅粉
            "quote_text": "#880e4f",   # 引用文字：深玫红
            "tag": "#ad1457",          # 标签色：深粉
        }
    },
    1: {  # 周二 · 养生生活 - 清新绿色调
        "name": "养生生活",
        "theme": "中式轻养生，正在成为最易传播的日常内容",
        "keywords": ["养生", "中医", "食疗", "药食同源", "食谱", "饮食", "进补", "体质", "节气", "四季", "春季", "养肝", "健脾", "抗炎", "营养", "早餐", "晚餐"],
        "direction": "四季顺时养生（如春季防风护肝）、药食同源食谱、一日三餐怎么吃",
        "colors": {
            "primary": "#4caf50",
            "heading": "#2e7d32",
            "text": "#33691e",
            "strong": "#2e7d32",
            "strong_bg": "#e8f5e9",
            "quote_border": "#81c784",
            "quote_bg": "#f1f8e9",
            "quote_text": "#33691e",
            "tag": "#558b2f",
        }
    },
    2: {  # 周三 · 慢病管理 - 警示橙色调
        "name": "慢病管理",
        "theme": "三高、心血管等慢性病，正在成为最刚需的科普",
        "keywords": ["高血压", "高血糖", "高血脂", "三高", "糖尿病", "心梗", "中风", "脑梗", "心血管", "心脏病", "胆固醇", "血脂", "血糖", "血压", "慢性病", "服药", "用药"],
        "direction": "高血压/糖尿病怎么吃、用药常识（千万别犯的错）、慢病的日常监测与护理",
        "colors": {
            "primary": "#ff9800",
            "heading": "#e65100",
            "text": "#5d4037",
            "strong": "#e65100",
            "strong_bg": "#fff3e0",
            "quote_border": "#ffb74d",
            "quote_bg": "#fff8e1",
            "quote_text": "#e65100",
            "tag": "#ef6c00",
        }
    },
    3: {  # 周四 · 情绪养生 - 治愈紫色调
        "name": "情绪养生",
        "theme": "坏情绪比高血压更伤身，老年人的心理问题不容忽视",
        "keywords": ["抑郁", "焦虑", "失眠", "情绪", "心理健康", "孤独", "悲观", "心态", "老年痴呆", "阿尔茨海默", "记忆", "认知", "精神", "心理", "情绪管理"],
        "direction": "焦虑/抑郁的识别与应对、情绪急救方法、孤独感的排解、如何保持乐观心态",
        "colors": {
            "primary": "#9c27b0",
            "heading": "#6a1b9a",
            "text": "#4a148c",
            "strong": "#7b1fa2",
            "strong_bg": "#f3e5f5",
            "quote_border": "#ce93d8",
            "quote_bg": "#f3e5f5",
            "quote_text": "#6a1b9a",
            "tag": "#8e24aa",
        }
    },
    4: {  # 周五 · 生活品质 - 品质蓝色调
        "name": "生活品质",
        "theme": "银发族的消费升级，如何把钱花在刀刃上",
        "keywords": ["消费", "购物", "保健品", "营养品", "体检", "保险", "理财", "退休", "养老金", "省钱", "购物车", "礼物", "适老化", "产品", "测评", "避坑"],
        "direction": "健康消费避坑指南、适老化产品测评、如何科学选购保健品/家用医疗器械",
        "colors": {
            "primary": "#2196f3",
            "heading": "#1565c0",
            "text": "#0d47a1",
            "strong": "#1565c0",
            "strong_bg": "#e3f2fd",
            "quote_border": "#64b5f6",
            "quote_bg": "#e3f2fd",
            "quote_text": "#1565c0",
            "tag": "#1976d2",
        }
    },
    5: {  # 周六 · 科技健康 - 科技青色调
        "name": "科技健康",
        "theme": "AI与智能设备，正在改变老年人的健康管理方式",
        "keywords": ["手机", "APP", "智能", "科技", "AI", "人工智能", "健康码", "挂号", "预约", "视频", "微信", "网络", "智能手表", "血压计", "血糖仪", "健康监测"],
        "direction": "AI健康助手怎么用、智能监测设备推荐、科技如何帮老人老有所依",
        "colors": {
            "primary": "#00bcd4",
            "heading": "#00838f",
            "text": "#006064",
            "strong": "#00838f",
            "strong_bg": "#e0f7fa",
            "quote_border": "#4dd0e1",
            "quote_bg": "#e0f7fa",
            "quote_text": "#00838f",
            "tag": "#0097a7",
        }
    },
    6: {  # 周日 · 科普急救 - 紧急红色调
        "name": "科普急救",
        "theme": "关键时刻能救命的硬知识，是最能打动人心的内容",
        "keywords": ["急救", "心梗", "中风", "脑梗", "猝死", "心肺复苏", "急救常识", "家庭药箱", "常备药", "心脏病", "胸痛", "呼吸困难", "跌倒", "烫伤", "噎住", "异物"],
        "direction": "心脑血管疾病预防与急救、中风/心梗的识别与应对、家庭常备药品清单、用药安全指南",
        "colors": {
            "primary": "#f44336",
            "heading": "#c62828",
            "text": "#b71c1c",
            "strong": "#c62828",
            "strong_bg": "#ffebee",
            "quote_border": "#e57373",
            "quote_bg": "#ffebee",
            "quote_text": "#c62828",
            "tag": "#d32f2f",
        }
    }
}

# 兼容旧代码的 WEEKLY_THEMES
WEEKLY_THEMES = {k: {
    "name": v["name"],
    "theme": v["theme"],
    "keywords": v["keywords"],
    "direction": v["direction"]
} for k, v in STYLE_THEMES.items()}

KEYWORDS = ["健康", "养生", "中医", "运动", "睡眠", "心理", "情感", "饮食", "减肥", "健身", "血压", "血糖", "心脏", "癌症", "疫苗", "医院", "医生", "药品", "保健", "体检", "养老", "老年", "中年", "退休", "家庭", "婚姻", "孩子"]

# ========== Markdown → HTML 样式转换 ==========
def get_style_for_weekday(weekday):
    """获取当天主题的样式配色"""
    return STYLE_THEMES.get(weekday, STYLE_THEMES[0])["colors"]

def markdown_to_html(md_text, weekday):
    """Markdown 转 HTML，应用当天主题样式"""
    colors = get_style_for_weekday(weekday)
    
    # 1. Markdown 转 HTML
    html = markdown.markdown(md_text, extensions=['nl2br', 'sane_lists', 'fenced_code'])
    
    # 2. 应用样式
    # H2 大章节标题
    html = re.sub(
        r'<h2>(.*?)</h2>',
        f'<h2 style="margin: 1.5em 0 1em; padding-left: 15px; border-left: 4px solid {colors["primary"]}; font-size: 20px; font-weight: 600; color: {colors["heading"]};">\\1</h2>',
        html
    )
    
    # H3 子小节标题
    html = re.sub(
        r'<h3>(.*?)</h3>',
        f'<h3 style="margin: 1.5em 0 0.8em; font-size: 17px; font-weight: 600; color: {colors["heading"]};">\\1</h3>',
        html
    )
    
    # 段落
    html = re.sub(
        r'<p>(.*?)</p>',
        f'<p style="margin: 1.2em 0; line-height: 1.9; color: {colors["text"]}; font-size: 16px;">\\1</p>',
        html
    )
    
    # 重点加粗
    html = re.sub(
        r'<strong>(.*?)</strong>',
        f'<strong style="color: {colors["strong"]}; background: {colors["strong_bg"]}; padding: 2px 6px; border-radius: 3px;">\\1</strong>',
        html
    )
    
    # 引用块
    html = re.sub(
        r'<blockquote>(.*?)</blockquote>',
        f'<blockquote style="border-left: 4px solid {colors["quote_border"]}; background: {colors["quote_bg"]}; color: {colors["quote_text"]}; padding: 1em 1.5em; margin: 1.5em 0; border-radius: 0 8px 8px 0;">\\1</blockquote>',
        html,
        flags=re.DOTALL
    )
    
    # 列表
    html = re.sub(
        r'<ul>',
        f'<ul style="padding-left: 2em; line-height: 2.2; color: {colors["text"]};">',
        html
    )
    html = re.sub(
        r'<ol>',
        f'<ol style="padding-left: 2em; line-height: 2.2; color: {colors["text"]};">',
        html
    )
    
    # 处理话题标签（#开头的内容）
    # 找到文末的话题标签行
    tag_pattern = r'<p style="[^"]*">#([^<]+)</p>'
    html = re.sub(
        tag_pattern,
        f'<p style="color: {colors["tag"]}; font-size: 14px; margin-top: 2em;">#\\1</p>',
        html
    )
    
    # 包装在白色卡片容器中
    wrapped_html = f'''<section style="background: white; border-radius: 8px; padding: 20px 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
{html}
</section>'''
    
    return wrapped_html

# ========== 工具函数 ==========
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
                        log(f"[封面] 生成成功: {image_url}")
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

def generate_fallback_cover(theme_info):
    """降级方案：Pillow生成位图封面，颜色与主题一致"""
    log("[封面] 通义万相失败，启动降级方案（Pillow位图）")
    try:
        W, H = 1280, 720
        bg = Image.new("RGB", (W, H))
        draw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw
        theme_name = theme_info.get("name", "")
        if any(kw in theme_name for kw in ["情感", "心理", "孤独", "情绪"]):
            bg_color, accent1, accent2, text_color = "#1a1a2e", "#e94560", "#f1f1f1", "#f1f1f1"
        elif any(kw in theme_name for kw in ["养生", "食疗", "生活"]):
            bg_color, accent1, accent2, text_color = "#2d3436", "#00b894", "#fdcb6e", "#ffeaa7"
        elif any(kw in theme_name for kw in ["慢病", "健康", "医疗"]):
            bg_color, accent1, accent2, text_color = "#2c3e50", "#3498db", "#1abc9c", "#ecf0f1"
        elif any(kw in theme_name for kw in ["科技", "智能"]):
            bg_color, accent1, accent2, text_color = "#0f0f23", "#00d2ff", "#7b2ff7", "#f5f5f5"
        else:
            bg_color, accent1, accent2, text_color = "#2d3436", "#e17055", "#fdcb6e", "#f5f6fa"
        def hex_to_rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
        bg_rgb = hex_to_rgb(bg_color)
        for y in range(H):
            shade = int(20 * (1 - y / H))
            r = max(0, bg_rgb[0] - shade)
            g = max(0, bg_rgb[1] - shade)
            b = max(0, bg_rgb[2] - shade)
            for x in range(W):
                bg.putpixel((x, y), (r, g, b))
        d = draw(bg)
        d.ellipse([int(W*0.72), int(H*0.55), W+50, H+50], fill=hex_to_rgb(accent1), outline=None)
        d.ellipse([-60, -90, int(W*0.4), int(H*0.35)], fill=hex_to_rgb(accent2)+(64,), outline=None)
        try:
            from PIL import ImageFont
            font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
            font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except Exception:
            font_lg = ImageFont.load_default()
            font_sm = font_lg
        day_text = WEEKDAY_NAMES[beijing_now().weekday()]
        d.text((W//2, H//2 - 50), f"[ {day_text} ]", fill=hex_to_rgb(text_color), font=font_sm, anchor="mm")
        d.text((W//2, H//2 + 20), theme_info.get("name", "健康生活"), fill=(255,255,255), font=font_lg, anchor="mm")
        d.text((W//2, H//2 + 95), "HEALTH & WELLNESS", fill=hex_to_rgb(text_color), font=font_sm, anchor="mm")
        output = io.BytesIO()
        bg.save(output, format="PNG")
        b64 = base64.b64encode(output.getvalue()).decode("utf-8")
        log("[封面] 降级图片生成成功")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        log(f"[封面] 降级生成失败: {e}")
        return None

def get_access_token():
    if not WX_APPID or not WX_APPSECRET:
        log("[微信] 缺少 WX_APPID 或 WX_APPSECRET，跳过草稿箱推送")
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
    if image_url.startswith("data:"):
        log("[微信] 本地图片降级方案")
        match = re.match(r"data:image/\w+;base64,(.+)", image_url)
        if match:
            original_bytes = base64.b64decode(match.group(1))
        else:
            log("[微信] Base64 格式解析失败")
            return None
    else:
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
    tgt_w = 900
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
        log(f"[微信] media_id: {media_id}")
        return {"media_id": media_id, "url": thumb_url}
    log(f"[微信] 上传失败: {upload_result}")
    return None

def create_draft(access_token, title, author, digest, content_html, media_id, thumb_url=""):
    log(f"[微信] 创建草稿箱文章...")
    title_utf8 = len(title.encode("utf-8"))
    log(f"[微信] 标题: '{title}' ({len(title)}字, {title_utf8}B)")
    
    # 如果标题超长，使用智能截断（优先在标点处断开）
    if title_utf8 > 64:
        # 在 node2_title 已经限制在 60B 内，这里是双重保险
        title = truncate_title_smart(title, 64)
        log(f"[微信] 标题智能截断: '{title}' ({len(title.encode('utf-8'))}B)")
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
        log("[微信] 草稿创建成功！")
        return True
    log(f"[微信] 草稿创建失败: {result}")
    return False

def push_article_to_draft(title, author, digest, content_html, cover_url, weekday):
    access_token = get_access_token()
    if not access_token:
        return False
    media_result = upload_cover_for_draft(access_token, cover_url)
    if not media_result:
        return False
    return create_draft(access_token, title, author, digest, content_html,
                         media_result["media_id"], media_result.get("url", ""))

# ========== 提示词模板 ==========
THREE_HOOKS_SYSTEM = '你是一位顶级微信公众号爆款文章写作大师，擅长用"三把钩子"写作法创作高转发、高点赞的爆款文章。'

THREE_HOOKS_ARTICLE_PROMPT = """## 任务
根据以下大纲，写一篇微信公众号爆款文章。

## 标题
{title}

## 大纲
{outline}

## 写作要求
1. 字数：1200-1500字，结尾附5个话题标签 #话题标签
2. 去结构化：口语化，每段落不超过5行，不用1、2、3排序
3. 去AI味：不用首先/其次/再次/最后/总之/综上所述，不用破折号
4. 内容原创：严禁抄袭，有立场有情绪，不要中立
5. 排版：每段落不超过5行，可用emoji分段
6. 使用 Markdown 格式：
   - 用 ## 表示大章节标题
   - 用 ### 表示子小节标题
   - 用 **文字** 表示重点加粗
   - 用 > 表示引用/金句

### 三把钩子写作法
**第一把钩子**：开头一秒钩住读者——目标读者画像+扎心问题+痛点场景+好处承诺
**第二把钩子**：中间建立信任——核心观点+真实例子+底层逻辑（"其实……"开头）+对比反差
**第三把钩子**：结尾让人行动/收藏/转发——可操作步骤+亲身经历+金句收尾+互动提问

### 自检清单
- 开头命中痛点？例子有名字/细节/画面？解释"为什么"？读者知道第一步？
- 故事出现？结尾引发收藏/转发/留言？

直接输出 Markdown 格式正文，文末加5个话题标签。"""

SUMMARY_PROMPT = """## 任务
根据以下文章，生成80-90字的摘要。

## 标题
{title}

## 正文
{article}

要求：简洁有力，吸引点击。直接输出摘要。"""

COVER_PROMPT = """## 任务
根据以下文章，生成具有强烈视觉冲击力的AI绘画提示词。

## 标题
{title}

## 正文摘要
{article_summary}

## 视觉冲击要素（必须包含）

### 1. 核心主体（选1-2个）
- 具体人物（如：一位满头银发的老人、穿着白大褂的中年医生）
- 或具体场景（如：一碗冒着热气的中药汤、一个智能手表的特写镜头）

### 2. 情绪张力（必选）
从以下选择最能表达文章情感的1-2个：
- 孤独感 → 空旷留白、人物背影、窗外黄昏
- 温暖感 → 暖色光晕、家庭聚餐、牵手画面
- 紧迫感 → 逆光剪影、动态模糊、红色警示
- 专业感 → 医院场景、检测设备、数据可视化
- 科技感 → 霓虹灯光、未来风格、智能设备发光

### 3. 光影戏剧性（必选）
从以下选择2-3个组合：
- 黄金时段阳光（温暖、治愈）
- 逆光剪影（神秘、深邃）
- 霓虹灯光（科技、现代）
- 散射柔光（柔和、亲切）
- 明暗对比（戏剧感）
- 薄雾/光束（氛围感）

### 4. 色彩方案（必选）
选择1-2个主色调：
- 暖色调：橙色/金色/深红（温暖、养生）
- 冷色调：蓝色/青色（科技、专业）
- 中性色调：米白/浅灰（简洁、大气）
- 对比色：深蓝+金黄（视觉冲击）

### 5. 构图方式（必选）
选择1个：
- 特写+浅景深（聚焦主体，背景虚化）
- 黄金分割（主体在视觉重心）
- 对角线构图（动感、活力）
- 框架构图（用门窗框住主体）
- 俯拍+俯视（宏观、全景感）

### 6. 风格定位
- 摄影风格：电影感纪实、杂志封面、复古胶片
- 插画风格：扁平插画、水墨国风、治愈系插画
- 混合风格：光影插画、拼贴艺术

### 7. 技术参数
- 比例：16:9（宽屏电影感）
- 分辨率暗示词：超高清、8K质感、细节丰富
- 负面词排除：模糊、噪点、变形

## 输出格式
直接输出英文提示词（逗号分隔），200-300字，包含所有视觉要素。
禁止输出解释说明。"""

# ========== 流水线节点函数 ==========
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
    except:
        title, outline, source = "健康养生", "", "网络"
    log("[4] 生成正文(Markdown格式)...")
    result = call_deepseek(THREE_HOOKS_ARTICLE_PROMPT.format(title=title, outline=outline[:2000] or "基础大纲"),
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
        if token_data.get("code") != 0:
            log(f"[飞书] Token获取失败 code={token_data.get('code')}: {token_data.get('msg', '')}")
            return None
        if "tenant_access_token" not in token_data:
            log(f"[飞书] Token响应异常: {token_resp.text[:200]}")
            return None
        access_token = token_data["tenant_access_token"]
        
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
            # 文档已创建，返回链接
            doc_url = f"https://feishu.cn/docx/{doc_token}"
            log(f"[飞书] 文档链接: {doc_url}")
            return doc_url
        
        # 5. 生成分享链接
        share_url = f"https://feishu.cn/docx/{doc_token}"
        log(f"[飞书] 文档已创建: {share_url}")
        
        # 6. 写入多维表格
        table_id = ensure_articles_table(access_token)
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
            write_article_record(access_token, table_id, record_data)
        
        return share_url
        
    except Exception as e:
        log(f"[飞书] 推送异常: {e}")
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

# ========== Flask 路由 ==========
@app.route("/")
def index():
    return """✅ 内容流水线 v3.0（七天主题样式系统）
<br>• GET /trigger?force=1 → 强制触发完整流程
<br>• GET /test_draft → 测试草稿箱
<br>• GET /test_status → 检查配置
<br>• GET /test_style → 预览当天样式"""

@app.route("/test_feishu")
def test_feishu():
    """快速测试飞书连接和建表"""
    import traceback
    try:
        token = get_feishu_token()
        if not token:
            return jsonify({"ok": False, "error": "FEISHU_APP_ID 或 FEISHU_APP_SECRET 未配置"})
        
        table_id = ensure_articles_table(token)
        if not table_id:
            return jsonify({"ok": False, "error": "建表失败"})
        
        # 写一条测试记录
        import time
        test_record = {
            "date": int(time.time()),
            "weekday": "测试",
            "theme": "测试主题",
            "title": "【测试】流水线调试中",
            "summary": "这是一条测试记录，用于验证飞书多维表格写入功能是否正常。",
            "doc_url": "https://feishu.cn/docx/test",
            "cover_url": "",
            "source": "测试",
        }
        record_id = write_article_record(token, table_id, test_record)
        
        return jsonify({
            "ok": True,
            "table_id": table_id,
            "record_id": record_id,
            "message": "飞书连接正常，公众号文章记录表已就绪"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()}), 500

@app.route("/rename_article_table")
def rename_article_table():
    """重命名公众号文章记录表为公众号公众号文章记录"""
    import traceback
    try:
        token = get_feishu_token()
        if not token:
            return jsonify({"ok": False, "error": "FEISHU_APP_ID 或 FEISHU_APP_SECRET 未配置"})
        
        headers = {"Authorization": f"Bearer {token}"}
        table_id = FEISHU_ARTICLES_TABLE_ID or "tbl3jVfVkQZwlyIv"
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}"
        resp = requests.patch(url, headers=headers, json={"name": "公众号公众号文章记录"}, timeout=10)
        data = resp.json()
        
        if data.get("code") != 0:
            return jsonify({"ok": False, "error": data})
        
        return jsonify({"ok": True, "message": "表名已改为：公众号公众号文章记录"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()}), 500

@app.route("/test_status")
def test_status():
    return jsonify({
        "WX_APPID": "✅" if WX_APPID else "❌ 未配置",
        "WX_APPSECRET": "✅" if WX_APPSECRET else "❌ 未配置",
        "SERVERCHAN_KEY": "✅" if SERVERCHAN_KEY else "❌",
        "WANXIANG_API_KEY": "✅" if WANXIANG_API_KEY else "❌",
        "DEEPSEEK_API_KEY": "✅" if DEEPSEEK_API_KEY else "❌",
    })

@app.route("/test_style")
def test_style():
    """预览当天主题样式"""
    weekday = beijing_now().weekday()
    colors = get_style_for_weekday(weekday)
    theme = STYLE_THEMES[weekday]
    
    sample_md = """## 这是一个大章节标题

这是一段正文内容。**这是重点加粗的文字**，需要突出显示。

### 这是一个子小节

> 这是一句金句引用，需要特别突出。

正文继续，列表如下：

- 列表项一
- 列表项二
- 列表项三

#话题标签一 #话题标签二"""
    
    html = markdown_to_html(sample_md, weekday)
    
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>今日样式预览</title></head>
<body style="background: #f9f9f9; padding: 20px; font-family: sans-serif;">
<h2>📅 {WEEKDAY_NAMES[weekday]} · {theme['name']}</h2>
<p>主色调: <span style="color: {colors['primary']};">■</span> {colors['primary']}</p>
<p>标题色: <span style="color: {colors['heading']};">■</span> {colors['heading']}</p>
<p>正文色: <span style="color: {colors['text']};">■</span> {colors['text']}</p>
<hr>
{html}
</body></html>"""

@app.route("/test_draft")
def test_draft():
    log("=" * 50)
    log("🧪 草稿箱测试")
    log("=" * 50)
    weekday = beijing_now().weekday()
    
    cover_url = generate_cover_image(
        "An elderly Chinese woman sitting by the window, looking out at a quiet neighborhood, warm afternoon sunlight, gentle and peaceful atmosphere, realistic photography style, 16:9"
    )
    if not cover_url:
        return jsonify({"success": False, "error": "封面图生成失败"}), 500
    
    sample_md = """## 子女不在身边，老人如何告别孤独感？

李阿姨今年68岁，退休前是小学老师。老伴三年前走了，儿子在上海工作，一年回来两三次。

她说，**最难熬的不是夜里醒来的那两个小时，而是白天**。手机里儿子的照片看了又看，想打电话又怕打扰他工作。

### 空巢老人的三个解法

> 老有所依，不是物质上的依靠，是心里的那份牵挂。

那怎么办？

- 给自己找个"寄托"，养花养鸟养猫狗都行
- 主动走出去，小区广场舞队、棋牌室都是好去处
- 学会用微信视频，能看见脸的距离感小很多

这是很多空巢老人的真实写照。**孤独感对老年人的伤害，比我们想象的大得多**。

#空巢老人 #孤独感 #心理健康 #家庭关系 #养老"""
    
    article_html = markdown_to_html(sample_md, weekday)
    
    success = push_article_to_draft(
        "子女不在身边，老人如何告别孤独感？",
        STYLE_THEMES[weekday]["name"],
        "子女不在身边，空巢老人的孤独感如何化解？这三个方法值得尝试。",
        article_html,
        cover_url,
        weekday
    )
    if success:
        send_to_wechat("✅ 草稿箱推送成功", f"📝 《子女不在身边，老人如何告别孤独感？》已推送\n🎨 封面：{cover_url}")
        return jsonify({"success": True, "cover_url": cover_url, "weekday": WEEKDAY_NAMES[weekday], "theme": STYLE_THEMES[weekday]["name"]})
    return jsonify({"success": False, "error": "草稿箱推送失败"}), 500

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
