from flask import Flask, jsonify
import os
import json
from datetime import datetime
import requests

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))
DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Server酱配置
SERVERCHAN_KEY = "SCT333499TpvZQWzbvJcMfDxo7BmL8MsrV"

# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-6e2b402410694b50af206daee4f017bc"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# 健康养生相关关键词
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

def score_item(title):
    """计算标题与健康养生的相关度"""
    score = 0
    for kw in KEYWORDS:
        if kw in title:
            score += 2
    if "？" in title or "?" in title:
        score += 1
    return score

# ========== 三把钩子提示词 ==========

THREE_HOOKS_SYSTEM = """你是一位顶级微信公众号爆款文章写作大师，擅长用"三把钩子"写作法创作高转发、高点赞的爆款文章。

三把钩子写作法：
1. 第一把钩子：谁会在看第一眼觉得"这说的是我"？→ 解决标题和开头，用具体场景戳痛点
2. 第二把钩子：我凭什么让别人相信？→ 解决信任感，用真实案例+底层逻辑
3. 第三把钩子：看完后别人能带走什么？→ 解决收藏转发，用具体步骤+金句

风格要求：
- 语言接地气，像在跟朋友聊天
- 善用具体场景和细节
- 有温度，有共鸣，不说教
- 结尾要有让人想转发的金句"""

THREE_HOOKS_TITLE_PROMPT = """## 任务
根据以下热榜话题，用三把钩子法生成5个爆款标题，并选出最优的一个。

## 热榜话题
{hot_topics}

## 要求
1. 标题要符合微信公众号爆款风格
2. 具有强吸引力，能瞬间抓住读者眼球
3. 要有"这说的是我"的感觉
4. 最终标题不超过30个中文字符

## 输出格式
候选标题（5个）：
1. xxx
2. xxx
3. xxx
4. xxx
5. xxx

【最终标题】：xxx"""

THREE_HOOKS_OUTLINE_PROMPT = """## 任务
根据以下主题，用三把钩子法生成一篇文章大纲。

## 文章主题
标题：{title}
来源：{source}热榜

## 三把钩子详细展开

### 第一把钩子：谁会觉得"这说的是我"？
### 第二把钩子：凭什么让人相信？
### 第三把钩子：看完能带走什么？

## 输出格式
【目标读者】【核心金句】【文章结构】【小标题】"""

THREE_HOOKS_ARTICLE_PROMPT = """## 任务
根据以下大纲，写一篇微信公众号爆款文章。

## 标题
{title}

## 大纲
{outline}

## 写作要求（必须严格遵守）

### 基本要求
1. 字数：1200-1500字
2. 结尾：生成5个与正文匹配的话题标签，格式：#话题标签

### 去结构化
- 遵循真实阅读节奏，不要用论文结构
- 打散预设式结构，让表达更自然
- 用口语化表达，贴近真实说话的感觉

### 去AI味
- 不用AI高频词：首先、其次、再次、最后、总之、综上所述、值得注意的是、需要强调的是
- 不用破折号——
- 不用完美句式，加入不规则表达
- 减少排比句和对仗句

### 内容原创
- 严禁抄袭，基于大纲剖析从零创作
- 运用知识储备与创意构建内容
- 避免重复已有内容

### 敏感词规避
- 杜绝公众号敏感词、违禁词
- 避免医疗广告词、夸大宣传词
- 不用"根治"、"神效"、"必看"等词

### 有立场有情绪
- 允许有立场和情绪，不要中立
- 加入人味噪点：轻微犹豫、自我修正、吐槽、感叹
- 用主观判断替代中立说明
- 避免极端或失真

### 排版要求
- 不要用1、2、3排序结构
- 每段落≤5行，适宜手机阅读
- 可用emoji分段，但不过度
- 小标题简洁有力

### 三把钩子自检
- 开头：是否命中具体痛点？
- 中间：有真实例子和底层逻辑吗？
- 结尾：有具体步骤/金句/互动问题吗？

## 输出格式
直接输出正文内容，文末添加5个话题标签。"""

SUMMARY_PROMPT = """## 任务
根据以下文章，生成一个80-90字的微信公众号内容摘要。

## 文章标题
{title}

## 文章正文
{article}

## 要求
1. 字数：80-90字
2. 风格：简洁有力，吸引点击
3. 不要写"本文"、"这篇文章"等开头
4. 直击痛点，突出价值

直接输出摘要文字。"""

COVER_PROMPT = """## 任务
根据以下文章，生成一个公众号封面图的AI绘画提示词。

## 文章标题
{title}

## 文章主题
{article_summary}

## 虚实相生绘画框架

### 实（具体可感的视觉元素）
- 人物：文章面向的读者群像（如：中老年人的手、子女搀扶父母的背影）
- 神态：表情和情绪（如：眉头舒展、眼神坚定、嘴角微笑）
- 行为：具体动作（如：清晨打太极、围坐聊天、翻看日历）
- 环境：生活场景（如：社区公园、家庭客厅、医院走廊、菜市场）

### 虚（氛围和情感）
- 光影：清晨阳光、傍晚暖光、夜间台灯
- 色彩：主色调（如：温暖的橙黄色、清新的淡绿色）
- 情绪：整体感受（如：宁静、温馨、关怀、希望）
- 风格：写实插画风、摄影感、国潮风、治愈系

## 比例要求
画幅比例：16:9（横向构图，适合公众号封面）

## 输出格式
直接输出英文提示词，包含：主体人物和动作、环境场景、光影色彩氛围、艺术风格、比例和画质要求。

示例：
"A middle-aged woman with gentle smile, holding a cup of herbal tea, sitting by the window in soft morning light. Warm golden tones, cozy home environment with potted plants. Photorealistic illustration style, 16:9 aspect ratio, high detail."

直接输出英文提示词。"""

# ========== 节点函数 ==========

def node1_collector():
    """采集三大平台热榜"""
    all_items = []
    
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
            all_items.append({"title": title, "source": "百度", "score": score_item(title)})
        log(f"[1] 百度: {len([i for i in all_items if i['source']=='百度'])}条")
    except Exception as e:
        log(f"[1] 百度采集失败: {e}")
    
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
            all_items.append({"title": title, "source": "微博", "score": score_item(title)})
        log(f"[1] 微博: {len([i for i in all_items if i['source']=='微博'])}条")
    except Exception as e:
        log(f"[1] 微博采集失败: {e}")
    
    try:
        log("[1] 采集今日头条热榜...")
        r = requests.get(
            "https://www.toutiao.com/hot-list/hot-board/",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        data = r.json()
        for item in data.get("data", [])[:30]:
            title = item.get("Title", "")
            all_items.append({"title": title, "source": "头条", "score": score_item(title)})
        log(f"[1] 头条: {len([i for i in all_items if i['source']=='头条'])}条")
    except Exception as e:
        log(f"[1] 头条采集失败: {e}")
    
    relevant = [i for i in all_items if i["score"] > 0]
    relevant.sort(key=lambda x: x["score"], reverse=True)
    top5 = relevant[:5]
    
    if not top5:
        top5 = [
            {"title": "中老年人如何科学养生？", "source": "默认", "score": 3},
            {"title": "老年人睡眠不好怎么办？", "source": "默认", "score": 3},
        ]
    
    with open(f"{DATA_DIR}/candidates.json", "w", encoding="utf-8") as f:
        json.dump({"items": top5}, f, ensure_ascii=False)
    
    log(f"[1] 采集完成: 共{len(all_items)}条, 相关{len(relevant)}条")
    return top5

def node2_title():
    """生成标题"""
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            items = json.load(f)["items"]
        hot_topics = "\n".join([f"- {item['title']} ({item['source']})" for item in items])
    except:
        hot_topics = "中老年人如何科学养生？"
        items = [{"title": "健康养生", "source": "默认"}]
    
    log("[2] 生成标题...")
    prompt = THREE_HOOKS_TITLE_PROMPT.format(hot_topics=hot_topics)
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, temperature=0.8)
    
    final_title = None
    if result:
        lines = result.split("\n")
        for line in lines:
            if "最终标题" in line or "【最终标题】" in line:
                title = line.split("】")[-1].strip()
                if not title:
                    parts = line.split("：")
                    if len(parts) > 1:
                        title = parts[-1].strip()
                if title and len(title) <= 35:
                    final_title = title
                    break
        
        if not final_title:
            for line in lines:
                line = line.strip()
                if line and len(line) > 5 and not line.startswith("候选"):
                    final_title = line.strip("0123456789.、、★ ")
                    if len(final_title) <= 35:
                        break
    
    if final_title:
        while len(final_title.encode('utf-8')) > 60 and len(final_title) > 10:
            final_title = final_title[:-1]
    else:
        topic = items[0]["title"] if items else "健康养生"
        final_title = f"医生不会告诉你的{topic}真相"
    
    with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
        json.dump({"title": final_title}, f, ensure_ascii=False)
    log(f"[2] ✅ 标题: {final_title}")
    return final_title

def node3_outline():
    """生成大纲"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            source = json.load(f)["items"][0].get("source", "网络")
    except:
        title = "健康养生文章"
        source = "网络"
    
    log("[3] 生成大纲...")
    prompt = THREE_HOOKS_OUTLINE_PROMPT.format(title=title, source=source)
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, temperature=0.7)
    
    if result:
        with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
            json.dump({"outline": result, "title": title}, f, ensure_ascii=False)
        log(f"[3] ✅ 大纲: {len(result)}字")
        return result
    
    outline = "【目标读者】中老年人\n【核心金句】健康最重要\n【结构】引言-问题-解读-建议-结语"
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump({"outline": outline, "title": title}, f, ensure_ascii=False)
    return outline

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
        title = "健康养生文章"
        outline = ""
        source = "网络"
    
    log("[4] 生成正文...")
    prompt = THREE_HOOKS_ARTICLE_PROMPT.format(title=title, outline=outline[:2000] if outline else "基础大纲")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, temperature=0.8, max_tokens=3000)
    
    if result:
        article = result
    else:
        article = f"【{title}】\n\n这是一篇关于健康养生的文章。\n\n#健康 #养生 #中老年"
    
    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({"title": title, "article": article, "source": source}, f, ensure_ascii=False)
    log(f"[4] ✅ 正文: {len(article)}字")
    return article

def node5_summary_and_cover():
    """生成摘要和封面提示词"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article = json.load(f)["article"]
    except:
        title = "健康养生文章"
        article = "健康养生内容"
    
    log("[5] 生成摘要...")
    summary_prompt = SUMMARY_PROMPT.format(title=title, article=article[:2000])
    summary_result = call_deepseek(summary_prompt, "专业微信公众号运营专家", temperature=0.6, max_tokens=300)
    summary = summary_result.strip() if summary_result else f"{title}，教你科学养生方法。"
    
    log("[5] 生成封面提示词...")
    cover_prompt_text = COVER_PROMPT.format(title=title, article_summary=summary)
    cover_result = call_deepseek(cover_prompt_text, "AI绘画提示词工程师", temperature=0.8, max_tokens=500)
    cover_prompt = cover_result.strip() if cover_result else "A healthy lifestyle scene with warm lighting, 16:9, high quality."
    
    with open(f"{DATA_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cover_prompt": cover_prompt}, f, ensure_ascii=False)
    
    log(f"[5] ✅ 摘要: {len(summary)}字")
    log(f"[5] ✅ 封面提示词已生成")
    return summary, cover_prompt

def node6_send():
    """发送内容"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article_data = json.load(f)
            article = article_data["article"]
            source = article_data.get("source", "网络")
        with open(f"{DATA_DIR}/summary.json", encoding="utf-8") as f:
            summary_data = json.load(f)
            summary = summary_data.get("summary", "")
            cover_prompt = summary_data.get("cover_prompt", "")
    except:
        title = "健康养生文章"
        article = "内容"
        source = "网络"
        summary = ""
        cover_prompt = ""
    
    result = send_to_wechat(
        title=f"📝 新文章：{title}",
        content=f"""📊 **来源：** {source}热榜

🏷️ **标题：** {title}

📋 **摘要：** {summary}

━━━━━━━━━━━━━━━

📄 **正文：**
{article}

━━━━━━━━━━━━━━━

🎨 **封面图提示词：**
{cover_prompt}

━━━━━━━━━━━━━━━
👆 以上是今日生成的文章内容"""
    )
    
    if result.get("code") == 0:
        log("[6] ✅ 发送成功！")
        return {"status": "success", "message": "已发送到微信"}
    else:
        return {"status": "failed", "error": result}

@app.route("/")
def index():
    return "✅ 内容生产流水线"

@app.route("/trigger")
def trigger():
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
        
        log("="*50)
        log("🏁 流水线完成")
        log("="*50)
        
        return jsonify({"success": True, "result": result})
    except Exception as e:
        log(f"错误: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
