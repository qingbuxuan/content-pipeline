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

## 虚实相生框架
- 实：人物、神态、行为、环境
- 虚：光影、色彩、情绪、风格
- 比例：16:9

直接输出中文提示词。"""

# ========== 节点函数 ==========

def node1_collector():
    """采集热榜"""
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
            all_items.append({"title": title, "source": "微博", "score": score_item(title)})
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
            all_items.append({"title": title, "source": "头条", "score": score_item(title)})
    except Exception as e:
        log(f"[1] 头条失败: {e}")
    
    relevant = [i for i in all_items if i["score"] > 0]
    relevant.sort(key=lambda x: x["score"], reverse=True)
    top5 = relevant[:5] if relevant else [{"title": "中老年人如何科学养生？", "source": "默认", "score": 3}]
    
    with open(f"{DATA_DIR}/candidates.json", "w", encoding="utf-8") as f:
        json.dump({"items": top5}, f, ensure_ascii=False)
    
    log(f"[1] ✅ 采集完成: {len(top5)}条")
    return top5

def node2_title():
    """生成标题"""
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            items = json.load(f)["items"]
        hot_topics = "\n".join([f"- {i['title']}" for i in items])
    except:
        hot_topics = "健康养生"
        items = [{"title": "健康养生"}]
    
    log("[2] 生成标题...")
    result = call_deepseek(THREE_HOOKS_TITLE_PROMPT.format(hot_topics=hot_topics), THREE_HOOKS_SYSTEM, 0.8)
    
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
        title, source = "健康养生", "网络"
    
    log("[3] 生成大纲...")
    result = call_deepseek(THREE_HOOKS_OUTLINE_PROMPT.format(title=title, source=source), THREE_HOOKS_SYSTEM, 0.7)
    
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump({"outline": result or "基础大纲", "title": title}, f, ensure_ascii=False)
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
            title = json.load(f)["title"]
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
    
    content = f"""📊 **来源：** {source}热榜

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
