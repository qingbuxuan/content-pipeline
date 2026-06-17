# -*- coding: utf-8 -*-
"""通用工具函数：日志、推送、DeepSeek API、封面图生成"""
from config import *
import requests, base64, time

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

def get_current_season():
    """获取当前季节（中文），基于北京时间"""
    now = beijing_now()
    month = now.month
    if month in (3, 4, 5):
        return "春季"
    elif month in (6, 7, 8):
        return "夏季"
    elif month in (9, 10, 11):
        return "秋季"
    else:  # 12, 1, 2
        return "冬季"

def get_season_info():
    """返回当前季节的详细信息：名称、关键词、内容指导"""
    season = get_current_season()
    info = {
        "春季": {
            "keywords": ["春风", "养肝", "护肝", "过敏性鼻炎", "春困", "踏青", "换季", "流感", "升阳", "疏肝"],
            "guidance": "内容侧重：防风护肝、缓解春困、换季过敏、踏青运动、春季饮食（少酸多甘）、预防流感。",
            "avoid": "不要出现消暑、防寒保暖、贴秋膘等夏/秋/冬专属内容。"
        },
        "夏季": {
            "keywords": ["防暑", "降温", "空调病", "中暑", "夏季饮食", "防晒", "心火", "祛湿", "三伏天", "冷饮"],
            "guidance": "内容侧重：防暑降温、空调病预防、夏季饮食（清淡祛湿）、防晒护肤、心火调理、三伏天养生。",
            "avoid": "不要出现养肝、贴秋膘、保暖防寒等春/秋/冬专属内容。"
        },
        "秋季": {
            "keywords": ["润肺", "防燥", "贴秋膘", "秋乏", "早晚温差", "落叶", "燥邪", "养肺", "秋分", "进补"],
            "guidance": "内容侧重：润肺防燥、贴秋膘适度、应对早晚温差、缓解秋乏、秋季饮食（少辛多酸）、情绪调适。",
            "avoid": "不要出现养肝、防暑降温、保暖防寒等春/夏/冬专属内容。"
        },
        "冬季": {
            "keywords": ["保暖", "防寒", "冬季进补", "心脑血管", "流感", "藏精", "肾气", "三九天", "暖胃", "冬病夏治"],
            "guidance": "内容侧重：保暖防寒、冬季进补（适度不过量）、心脑血管防护、预防流感、藏精养肾、暖胃饮食。",
            "avoid": "不要出现养肝、防暑、润肺等春/夏/秋专属内容。"
        }
    }
    return season, info.get(season, {})

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
