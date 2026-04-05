from flask import Flask, jsonify
import os
import json
from datetime import datetime
import requests
import base64
import hashlib
import hmac
import time
import urllib.parse

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))
DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Server酱配置
SERVERCHAN_KEY = "SCT333499TpvZQWzbvJcMfDxo7BmL8MsrV"

# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-6e2b402410694b50af206daee4f017bc"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# 通义万相 API配置
WANXIANG_API_KEY = "sk-de7984bb01c84a2bb136167006864fe2"

# ========== 每周主题配置 ==========
WEEKLY_THEMES = {
    0: {  # 周一
        "name": "情感心理",
        "theme": "面对空巢与孤独，老人的情感需求正在被看见",
        "keywords": ["孤独", "空巢", "独居", "陪伴", "代际", "子女", "父母", "养老", "思念", "老年", "退休", "情感", "亲情", "家庭", "寂寞"],
        "direction": "如何面对独居/空巢/孤独感、代际沟通（如何与子女相处）"
    },
    1: {  # 周二
        "name": "养生生活",
        "theme": "中式轻养生，正在成为最易传播的日常内容",
        "keywords": ["养生", "中医", "食疗", "药食同源", "食谱", "饮食", "进补", "体质", "节气", "四季", "春季", "养肝", "健脾", "抗炎", "营养", "早餐", "晚餐"],
        "direction": "四季顺时养生（如春季防风护肝）、药食同源食谱、一日三餐怎么吃"
    },
    2: {  # 周三
        "name": "慢病管理",
        "theme": "三高、心血管等慢性病，正在成为最刚需的科普",
        "keywords": ["高血压", "高血糖", "高血脂", "三高", "糖尿病", "心梗", "中风", "脑梗", "心血管", "心脏病", "胆固醇", "血脂", "血糖", "血压", "慢性病", "服药", "用药"],
        "direction": "高血压/糖尿病怎么吃、用药常识（千万别犯的错）、慢病的日常监测与护理"
    },
    3: {  # 周四
        "name": "情绪养生",
        "theme": "坏情绪比高血压更伤身，老年人的心理问题不容忽视",
        "keywords": ["抑郁", "焦虑", "失眠", "情绪", "心理健康", "孤独", "悲观", "心态", "老年痴呆", "阿尔茨海默", "记忆", "认知", "精神", "心理", "情绪管理"],
        "direction": "焦虑/抑郁的识别与应对、情绪急救方法、孤独感的排解、如何保持乐观心态"
    },
    4: {  # 周五
        "name": "生活品质",
        "theme": "银发族的消费升级，如何把钱花在刀刃上",
        "keywords": ["消费", "购物", "保健品", "营养品", "体检", "保险", "理财", "退休", "养老金", "省钱", "购物车", "礼物", "适老化", "产品", "测评", "避坑"],
        "direction": "健康消费避坑指南、适老化产品测评、如何科学选购保健品/家用医疗器械"
    },
    5: {  # 周六
        "name": "科技健康",
        "theme": "AI与智能设备，正在改变老年人的健康管理方式",
        "keywords": ["手机", "APP", "智能", "科技", "AI", "人工智能", "健康码", "挂号", "预约", "视频", "微信", "网络", "智能手表", "血压计", "血糖仪", "健康监测"],
        "direction": "AI健康助手怎么用、智能监测设备推荐、科技如何帮老人老有所依"
    },
    6: {  # 周日
        "name": "科普急救",
        "theme": "关键时刻能救命的硬知识，是最能打动人心的内容",
        "keywords": ["急救", "心梗", "中风", "脑梗", "猝死", "心肺复苏", "急救常识", "家庭药箱", "常备药", "心脏病", "胸痛", "呼吸困难", "跌倒", "烫伤", "噎住", "异物"],
        "direction": "心脑血管疾病预防与急救、中风/心梗的识别与应对、家庭常备药品清单、用药安全指南"
    }
}

# 健康养生相关关键词（通用备选）
KEYWORDS = ["健康", "养生", "中医", "运动", "睡眠", "心理", "情感", "饮食", "减肥", "健身", "血压", "血糖", "心脏", "癌症", "疫苗", "医院", "医生", "药品", "保健", "体检", "养老", "老年", "中年", "退休", "家庭", "婚姻", "孩子"]

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

def send_to_wechat(title, content):
    """通过 Server酱 发送微信通知"""
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        data = {"title": title, "desp": content}
        resp = requests.post(url, data=data, timeout=10)
        result = resp.json()
        log(f"[推送] 发送结果: {result}")
        return result
    except Exception as e:
        log(f"[推送] 发送失败: {e}")
        return {"code": -1, "msg": str(e)}

def call_deepseek(prompt, system_prompt="你是一个有用的助手", temperature=0.7, max_tokens=2500):
    """调用 DeepSeek API"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=180)
        result = resp.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            log(f"[DeepSeek] API错误: {result}")
            return None
    except Exception as e:
        log(f"[DeepSeek] 调用失败: {e}")
        return None

def generate_cover_image(prompt):
    """调用通义万相生成封面图"""
    try:
        log(f"[封面] 生成封面图...")
        
        # 通义万相 API (使用阿里云百炼)
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WANXIANG_API_KEY}",
            "X-DashScope-Async": "enable"
        }
        
        payload = {
            "model": "wanx-v1",
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "style": "<auto>",
                "size": "1280*720",  # 16:9 横屏
                "n": 1
            }
        }
        
        # 发起生成请求
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        result = resp.json()
        log(f"[封面] 任务创建: {result}")
        
        if "output" in result and "task_id" in result["output"]:
            task_id = result["output"]["task_id"]
            
            # 轮询等待结果
            for i in range(30):  # 最多等待30次
                time.sleep(3)
                
                status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
                status_resp = requests.get(status_url, headers={"Authorization": f"Bearer {WANXIANG_API_KEY}"})
                status_result = status_resp.json()
                
                task_status = status_result.get("output", {}).get("task_status", "")
                log(f"[封面] 状态: {task_status}")
                
                if task_status == "SUCCEEDED":
                    # 获取图片URL
                    results = status_result.get("output", {}).get("results", [])
                    if results and len(results) > 0:
                        image_url = results[0].get("url", "")
                        log(f"[封面] ✅ 生成成功: {image_url}")
                        return image_url
                elif task_status == "FAILED":
                    log(f"[封面] 生成失败: {status_result}")
                    return None
            
            log("[封面] 超时")
            return None
        else:
            log(f"[封面] 创建失败: {result}")
            return None
            
    except Exception as e:
        log(f"[封面] 异常: {e}")
        return None

def score_item(title):
    """计算标题与健康养生的相关度"""
    score = 0
    for kw in KEYWORDS:
        if kw in title:
            score += 2
    if "？" in title or "?" in title:
        score += 1
    return score

# ========== 提示词 ==========

THREE_HOOKS_SYSTEM = """你是一位顶级微信公众号爆款文章写作大师，擅长用"三把钩子"写作法创作高转发、高点赞的爆款文章。"""

THREE_HOOKS_TITLE_PROMPT = """## 任务
根据以下热榜话题，生成5个爆款标题，选出最优的一个。

## 热榜话题
{hot_topics}

## 要求
1. 标题要符合微信公众号爆款风格
2. 具有强吸引力，能瞬间抓住读者眼球
3. 最终标题不超过30个中文字符

## 输出格式
候选标题（5个）：
1. xxx
2. xxx
3. xxx
4. xxx
5. xxx

【最终标题】：xxx"""

THREE_HOOKS_OUTLINE_PROMPT = """## 任务
根据以下主题，生成一篇文章大纲。

## 标题：{title}
## 来源：{source}热榜

## 输出格式
【目标读者】【核心金句】【文章结构】【小标题】"""

THREE_HOOKS_ARTICLE_PROMPT = """## 任务
根据以下大纲，写一篇微信公众号爆款文章。

## 标题
{title}

## 大纲
{outline}

## 写作要求

### 基本要求
1. 字数：1200-1500字
2. 结尾：生成5个话题标签，格式：#话题标签

### 去结构化
- 遵循真实阅读节奏，不要用论文结构
- 用口语化表达，贴近真实说话的感觉

### 去AI味
- 不用AI高频词：首先、其次、再次、最后、总之、综上所述
- 不用破折号
- 不用完美句式

### 内容原创
- 严禁抄袭，从零创作
- 有立场有情绪，不要中立

### 排版要求
- 不要用1、2、3排序结构
- 每段落≤5行
- 可用emoji分段

### 三把钩子写作法

**第一把钩子：谁会在看第一眼的时候，觉得"这说的是我"？**
目标：开头，一秒钩住读者。
- 目标读者画像：此刻谁最需要这篇文章？描述一个具体的人（年龄、职业、正在为什么事失眠）。
- 扎心问题：他脑子里最疼的那个问题是什么？用他的语气写出来。
- 痛点场景：哪个日常瞬间会让这个问题爆发？
- 好处承诺：读完这篇文章，他能带走什么？（具体，不虚）

**第二把钩子：我凭什么让别人相信？**
目标：中间部分，用例子和逻辑建立信任。
- 核心观点：你想让他相信哪一句话？（一句话说透）
- 真实例子：有没有一个真实的人（自己/他人）能证明这个观点？名字（化名）、背景、他说过的一句话、一个具体画面。
- 底层逻辑：这个观点为什么成立？背后的原理/规律是什么？用"其实……"开头，揭示本质。
- 对比反差：有没有反面例子可以强化逻辑？

**第三把钩子：看完之后，别人能带走什么？**
目标：结尾部分，用步骤和故事让人行动、收藏、转发。
- 可操作步骤：如果他要行动，第一步做什么？第二步？第三步？动作具体，普通人能立刻执行。
- 亲身经历：你曾经怎么走过这条路？踩过什么坑？哪个瞬间让你觉醒？有情绪细节，能引发共鸣。
- 金句收尾：用一句话总结全文，让读者忍不住划线。简短、有力、可传播。
- 互动提问：抛一个问题，让读者愿意在评论区留言。

### 写作自检清单
写完每个部分，快速问自己：
- 开头：第一段有没有直接命中一个具体痛点？
- 例子：我举的例子有名字、有细节、有画面吗？
- 逻辑：我有没有解释"为什么"？（不只说"是什么"）
- 步骤：如果读者想照着做，他知道第一步是什么吗？
- 故事：我的个人经历出现了吗？有没有建立连接？
- 结尾：读者看完会想收藏/转发/留言吗？

直接输出正文内容，文末添加5个话题标签。"""

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

## 主题
{article_summary}

## 图像构思
- 主体：人物 / 建筑 / 静物 / 风景
- 场景：时间（黄昏 / 夜晚）、地点（街头 / 山间 / 室内）
- 光线：逆光、侧光、柔光、霓虹灯、窗边自然光…
- 风格：胶片感、日系、赛博朋克、纪实、商业人像等
- 构图：广角、特写、中景、俯拍、仰拍等

## 虚实相生框架
- 实：人物、神态、行为、环境
- 虚：光影、色彩、情绪、风格
- 比例：16:9

直接输出中文提示词。"""

# ========== 节点函数 ==========

def get_weekday_theme():
    """获取今天的星期主题"""
    weekday = datetime.now().weekday()  # 0=周一, 6=周日
    theme_info = WEEKLY_THEMES.get(weekday, WEEKLY_THEMES[0])
    log(f"[主题] 今天是周{weekday+1} · {theme_info['name']} · {theme_info['theme']}")
    return weekday, theme_info

def score_item(title, theme_keywords=None):
    """计算标题与主题的相关度"""
    score = 0
    title_lower = title.lower()
    
    # 通用关键词
    for kw in KEYWORDS:
        if kw in title:
            score += 1
    
    # 主题专属关键词
    if theme_keywords:
        for kw in theme_keywords:
            if kw in title:
                score += 3  # 主题关键词权重更高
    
    return score

def node1_collector():
    """采集热榜 + 主题匹配 + 网络搜索补充"""
    weekday, theme_info = get_weekday_theme()
    theme_keywords = theme_info["keywords"]
    theme_name = theme_info["name"]
    
    all_items = []
    
    # 从热榜采集
    try:
        log("[1] 采集百度热榜...")
        r = requests.get(
            "https://top.baidu.com/api/board/getBoard?boardId=realtime",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        data = r.json()
        for item in data.get("data", {}).get("content", [])[:30]:
            title = item.get("query", "")
            all_items.append({"title": title, "source": "百度", "score": score_item(title, theme_keywords)})
    except Exception as e:
        log(f"[1] 百度失败: {e}")
    
    try:
        log("[1] 采集微博热榜...")
        r = requests.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        data = r.json()
        for item in data.get("data", {}).get("realtime", [])[:30]:
            title = item.get("word", "")
            all_items.append({"title": title, "source": "微博", "score": score_item(title, theme_keywords)})
    except Exception as e:
        log(f"[1] 微博失败: {e}")
    
    try:
        log("[1] 采集头条热榜...")
        r = requests.get(
            "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"},
            timeout=10
        )
        data = r.json()
        for item in data.get("data", [])[:30]:
            title = item.get("Title", "")
            all_items.append({"title": title, "source": "头条", "score": score_item(title, theme_keywords)})
    except Exception as e:
        log(f"[1] 头条失败: {e}")
    
    # 按主题匹配度排序
    relevant = [i for i in all_items if i["score"] > 0]
    relevant.sort(key=lambda x: x["score"], reverse=True)
    top5 = relevant[:5] if relevant else []
    
    # 如果热榜素材不足，用网络搜索补充
    if len(top5) < 3:
        log("[1] 热榜素材不足，网络搜索补充...")
        search_results = web_search_for_theme(theme_info)
        for item in search_results:
            if item["title"] not in [i["title"] for i in top5]:
                top5.append({"title": item["title"], "source": "搜索", "score": 10})
    
    # 如果还是没有足够的素材，生成主题相关话题
    if len(top5) < 3:
        log("[1] 生成主题推荐话题...")
        generated = generate_theme_topics(theme_info)
        for item in generated:
            top5.append({"title": item, "source": f"{theme_name}推荐", "score": 5})
    
    with open(f"{DATA_DIR}/candidates.json", "w", encoding="utf-8") as f:
        json.dump({"items": top5, "weekday": weekday, "theme": theme_info}, f, ensure_ascii=False)
    
    log(f"[1] ✅ 采集完成: {len(top5)}条 ({theme_name})")
    return top5

def web_search_for_theme(theme_info):
    """网络搜索补充主题素材"""
    search_queries = [
        f"{theme_info['name']} 老年 最新",
        f"{theme_info['keywords'][0]} 老年人 热点",
        theme_info["direction"].split("、")[0] if theme_info["direction"] else theme_info["theme"]
    ]
    
    all_results = []
    for query in search_queries[:2]:
        try:
            log(f"[1] 搜索: {query}")
            # 用百度搜索（简单HTTP请求）
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.baidu.com/s?wd={encoded_query}&rn=10"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, headers=headers, timeout=10)
            
            # 简单解析标题（正则匹配）
            import re
            titles = re.findall(r'<h3[^>]*class="[^"]*c-title[^"]*"[^>]*>(.*?)</h3>', resp.text, re.DOTALL)
            for t in titles[:5]:
                clean = re.sub(r'<[^>]+>', '', t).strip()
                if clean and len(clean) > 5 and len(clean) < 50:
                    all_results.append({"title": clean})
        except Exception as e:
            log(f"[1] 搜索失败: {e}")
    
    return all_results[:5]

def generate_theme_topics(theme_info):
    """用AI生成主题相关话题"""
    prompt = f"""根据以下主题，生成3个适合中老年公众号的文章话题。

主题：{theme_info['theme']}
方向：{theme_info['direction']}

要求：
1. 话题要贴近中老年读者生活
2. 具有传播性和共鸣感
3. 每行一个话题，不要编号

直接输出3个话题："""
    
    result = call_deepseek(prompt, "你是一个专业的内容策划师", 0.8, 500)
    if result:
        lines = [l.strip() for l in result.split("\n") if l.strip() and len(l.strip()) > 5]
        return lines[:3]
    return []

def node2_title():
    """生成标题"""
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            data = json.load(f)
            items = data["items"]
            theme_info = data.get("theme", {})
        hot_topics = "\n".join([f"- {i['title']}" for i in items])
    except:
        hot_topics = "健康养生"
        items = [{"title": "健康养生"}]
        theme_info = {}
    
    # 构建带主题的提示词
    theme_context = f"\n\n## 今日主题\n主题名称：{theme_info.get('name', '健康养生')}\n主题方向：{theme_info.get('direction', '')}\n核心观点：{theme_info.get('theme', '')}"
    
    prompt = f"""## 任务
根据以下热榜话题，结合今日主题，生成5个爆款标题，选出最优的一个。

## 热榜话题
{hot_topics}
{theme_context}

## 要求
1. 标题要符合微信公众号爆款风格，紧扣今日主题「{theme_info.get('name', '健康养生')}」
2. 具有强吸引力，能瞬间抓住读者眼球
3. 最终标题不超过30个中文字符
4. 标题要引发情感共鸣，有代入感

## 输出格式
候选标题（5个）：
1. xxx
2. xxx
3. xxx
4. xxx
5. xxx

【最终标题】：xxx"""
    
    log("[2] 生成标题...")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, 0.8)
    
    final_title = None
    if result:
        for line in result.split("\n"):
            if "最终标题" in line:
                title = line.split("】")[-1].strip()
                if not title:
                    title = line.split("：")[-1].strip()
                if title and len(title) <= 50:
                    final_title = title
                    break
    
    if not final_title:
        final_title = items[0]["title"] if items else "健康养生"
    
    while len(final_title.encode('utf-8')) > 60:
        final_title = final_title[:-1]
    
    with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
        json.dump({"title": final_title, "theme": theme_info}, f, ensure_ascii=False)
    log(f"[2] ✅ 标题: {final_title}")
    return final_title

def node3_outline():
    """生成大纲"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            data = json.load(f)
            source = data["items"][0].get("source", "网络")
            theme_info = data.get("theme", {})
    except:
        title, source = "健康养生", "网络"
        theme_info = {}
    
    # 构建带主题的大纲提示词
    theme_context = f"\n\n## 今日主题「{theme_info.get('name', '健康养生')}」\n核心观点：{theme_info.get('theme', '')}\n推荐方向：{theme_info.get('direction', '')}"
    
    prompt = f"""## 任务
根据以下主题，生成一篇文章大纲。

## 标题：{title}
## 来源：{source}热榜
{theme_context}

## 输出格式
【目标读者】【核心金句】【文章结构】【小标题】"""
    
    log("[3] 生成大纲...")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, 0.7)
    
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump({"outline": result or "基础大纲", "title": title, "theme": theme_info}, f, ensure_ascii=False)
    log("[3] ✅ 大纲完成")
    return result

def node4_article():
    """生成正文"""
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
    result = call_deepseek(THREE_HOOKS_ARTICLE_PROMPT.format(title=title, outline=outline[:2000] or "基础大纲"), THREE_HOOKS_SYSTEM, 0.8, 3000)
    
    article = result or f"【{title}】\n\n这是一篇健康养生文章。\n\n#健康 #养生"
    
    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({"title": title, "article": article, "source": source}, f, ensure_ascii=False)
    log(f"[4] ✅ 正文: {len(article)}字")
    return article

def node5_summary_and_cover():
    """生成摘要和封面图"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article = json.load(f)["article"]
    except:
        title, article = "健康养生", "内容"
    
    # 摘要
    log("[5] 生成摘要...")
    summary = call_deepseek(SUMMARY_PROMPT.format(title=title, article=article[:2000]), "专业运营专家", 0.6, 300) or f"{title}，科学养生方法。"
    
    # 封面提示词
    log("[5] 生成封面提示词...")
    cover_prompt = call_deepseek(COVER_PROMPT.format(title=title, article_summary=summary), "AI绘画工程师", 0.8, 500) or "A healthy lifestyle scene, 16:9, high quality."
    
    # 生成封面图
    cover_url = generate_cover_image(cover_prompt)
    
    with open(f"{DATA_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cover_prompt": cover_prompt, "cover_url": cover_url}, f, ensure_ascii=False)
    
    log(f"[5] ✅ 摘要: {len(summary)}字")
    log(f"[5] ✅ 封面: {cover_url or '生成失败'}")
    return summary, cover_prompt, cover_url

def node6_send():
    """发送内容"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title_data = json.load(f)
            title = title_data["title"]
            theme_info = title_data.get("theme", {})
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article_data = json.load(f)
            article = article_data.get("article", "")
            source = article_data.get("source", "网络")
        with open(f"{DATA_DIR}/summary.json", encoding="utf-8") as f:
            data = json.load(f)
            summary = data.get("summary", "")
            cover_prompt = data.get("cover_prompt", "")
            cover_url = data.get("cover_url", "")
    except Exception as e:
        log(f"[6] 读取数据失败: {e}")
        title = "健康养生文章"
        article = "内容"
        source = "网络"
        summary = ""
        cover_url = ""
        cover_prompt = ""
        theme_info = {}
    
    theme_tag = f"📌 **今日主题：** {theme_info.get('name', '健康养生')} · {theme_info.get('theme', '')}"
    
    weekday, _ = get_weekday_theme()
    content = f"""📅 **周{weekday+1}** · {theme_info.get('name', '健康养生')}

{theme_tag}

📊 **素材来源：** {source}

━━━━━━━━━━━━━━━

🏷️ **标题：** {title}

📋 **摘要：** {summary}

━━━━━━━━━━━━━━━

📄 **正文：**
{article}

━━━━━━━━━━━━━━━

🎨 **封面图：** {cover_url or '生成失败'}

💡 **封面提示词：** {cover_prompt}

━━━━━━━━━━━━━━━
👆 以上是今日生成的文章内容"""
    
    result = send_to_wechat(f"📝 新文章：{title}", content)
    
    if result.get("code") == 0:
        log("[6] ✅ 发送成功！")
        return {"status": "success", "cover_url": cover_url}
    else:
        return {"status": "failed", "error": result}

@app.route("/")
def index():
    return "✅ 内容生产流水线 + 通义万相封面图"

@app.route("/trigger")
def trigger():
    # 每日只执行一次
    today = datetime.now().strftime('%Y%m%d')
    lock_file = f"{DATA_DIR}/executed_{today}.lock"
    
    if os.path.exists(lock_file):
        log("="*50)
        log("⏭️ 今日已执行，跳过")
        log("="*50)
        return jsonify({"success": True, "result": {"status": "skipped", "message": "今日已执行过"}})
    
    log("="*50)
    log("🚀 流水线启动")
    log("="*50)
    
    try:
        node1_collector()
        node2_title()
        node3_outline()
        node4_article()
        node5_summary_and_cover()
        result = node6_send()
        
        # 成功后创建锁文件
        with open(lock_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        log("="*50)
        log("🏁 流水线完成")
        log("="*50)
        
        return jsonify({"success": True, "result": result})
    except Exception as e:
        log(f"错误: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
