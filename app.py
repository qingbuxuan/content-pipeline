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

def call_deepseek(prompt, system_prompt="你是一个有用的助手", temperature=0.7):
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
            "max_tokens": 2000
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

## 三把钩子思考
第一把钩子：写给哪种具体的人？
- 不要写"中年人"，写"50岁、退休金3000、孙子要上兴趣班、医保卡不敢刷"的人
- 找准那个最痛的瞬间：凌晨惊醒、朋友圈攀比、被邻居炫耀刺激

第二把钩子：核心金句是什么？
- 一句话说透本质
- 让人想截图转发

第三把钩子：读者能带走什么？
- 一个方法/一句安慰/一个答案

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
请具体描述：
1. 这篇文章写给哪种人？（越具体越好：年龄、职业、生活状态、经济情况）
2. 他现在最痛的问题是什么？
3. 哪个日常瞬间会让这个问题爆发？（半夜惊醒、刷朋友圈、被@、聚会时...）
4. 读完文章，他能带走什么？（一个方法/一句安慰/一个答案）

### 第二把钩子：凭什么让人相信？
请具体描述：
1. 文章最核心的那句话是什么？（金句，一句话说完）
2. 有没有一个真实案例能证明？（化名、年龄、经历、说过的话）
3. 这句话背后的原理是什么？（用"其实..."开头）
4. 有没有反面例子能对比？

### 第三把钩子：看完能带走什么？
请具体描述：
1. 第一步做什么？第二步？第三步？（越具体越好）
2. 作者自己踩过什么坑？
3. 一句话收尾金句（让人想转发）
4. 结尾抛什么问题引发评论？

## 输出格式
用以下格式输出大纲：

【目标读者】
- 人群描述：xxx
- 痛点瞬间：xxx
- 带走收获：xxx

【核心金句】
xxx

【文章结构】
- 引言：xxx
- 第一部分：xxx（含案例+金句）
- 第二部分：xxx（含步骤+方法）
- 第三部分：xxx（含反思+共鸣）
- 结尾：xxx（金句+互动问题）

【小标题】（3-5个，用吸引人的方式命名）
"""

THREE_HOOKS_ARTICLE_PROMPT = """## 任务
根据以下大纲，用三把钩子写作法扩写成一篇完整的微信公众号爆款文章。

## 标题
{title}

## 大纲
{outline}

## 三把钩子写作自检清单

### 第一把钩子：谁会觉得"这说的是我"？
□ 开头第一段是否直接命中一个具体痛点？
□ 目标读者画像清晰吗？（年龄、职业、具体困境）
□ 痛点问题用读者语气写出来了吗？
□ 哪个日常瞬间让问题爆发？（凌晨惊醒/刷朋友圈/被@/聚会时...）
□ 好处承诺具体吗？

### 第二把钩子：我凭什么让别人相信？
□ 核心观点一句话说透了吗？
□ 有没有真实例子？（名字、背景、说过的话、具体画面）
□ 有没有用"其实..."揭示底层逻辑？
□ 有没有对比反差强化逻辑？
□ 中间部分有让人点头的例子吗？

### 第三把钩子：看完能带走什么？
□ 第一步/第二步/第三步具体可操作吗？
□ 有没有作者亲身经历的故事细节？
□ 有没有引发共鸣的情绪细节？
□ 结尾金句能让人划线/转发吗？
□ 互动问题能引发评论区留言吗？

## 正文写作要求
1. 字数：800-1200字
2. 格式：用emoji小标题分段
3. 语言：接地气，像跟朋友聊天
4. 开头：必须有强吸引力的钩子，一秒钩住读者
5. 中间：用例子+逻辑建立信任
6. 结尾：具体步骤+金句+互动问题

## 输出
直接输出完整文章正文，不需要其他说明。"""

# ========== 节点函数 ==========

def node1_collector():
    """采集三大平台热榜"""
    all_items = []
    
    # 1. 百度热榜
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
        log(f"[1] 百度: 获取{len([i for i in all_items if i['source']=='百度'])}条")
    except Exception as e:
        log(f"[1] 百度采集失败: {e}")
    
    # 2. 微博热榜
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
        log(f"[1] 微博: 获取{len([i for i in all_items if i['source']=='微博'])}条")
    except Exception as e:
        log(f"[1] 微博采集失败: {e}")
    
    # 3. 今日头条热榜
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
        log(f"[1] 头条: 获取{len([i for i in all_items if i['source']=='头条'])}条")
    except Exception as e:
        log(f"[1] 头条采集失败: {e}")
    
    # 筛选相关度最高的
    relevant = [i for i in all_items if i["score"] > 0]
    relevant.sort(key=lambda x: x["score"], reverse=True)
    top5 = relevant[:5]
    
    if not top5:
        top5 = [
            {"title": "中老年人如何科学养生？", "source": "默认", "score": 3},
            {"title": "老年人睡眠不好怎么办？", "source": "默认", "score": 3},
        ]
        log("[1] 无相关热榜，使用默认数据")
    
    with open(f"{DATA_DIR}/candidates.json", "w", encoding="utf-8") as f:
        json.dump({"items": top5}, f, ensure_ascii=False)
    
    log(f"[1] 采集完成: 共{len(all_items)}条, 相关{len(relevant)}条, 选用{len(top5)}条")
    return top5

def node2_title():
    """生成标题 - 使用三把钩子法"""
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            items = json.load(f)["items"]
        hot_topics = "\n".join([f"- {item['title']} (来源:{item['source']})" for item in items])
    except:
        hot_topics = "中老年人如何科学养生？\n老年人睡眠不好怎么办？\n退休后如何保持身心健康"
        items = [{"title": "中老年人如何科学养生？", "source": "默认"}]
    
    log("[2] 使用三把钩子法生成标题...")
    
    prompt = THREE_HOOKS_TITLE_PROMPT.format(hot_topics=hot_topics)
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, temperature=0.8)
    
    if result:
        log(f"[2] DeepSeek返回:\n{result[:500]}...")
        
        # 提取最终标题
        lines = result.split("\n")
        final_title = None
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
                if "★" in line or "⭐" in line or "最优" in line:
                    title = line.replace("★", "").replace("⭐", "").replace("最优", "").strip()
                    if title and len(title) <= 35:
                        final_title = title
                        break
        
        if not final_title:
            for line in lines:
                line = line.strip()
                if line and len(line) > 5 and not line.startswith("候选") and "标题" not in line[:5]:
                    final_title = line.strip("0123456789.、、 ")
                    if len(final_title) <= 35:
                        break
        
        if final_title:
            while len(final_title.encode('utf-8')) > 60 and len(final_title) > 10:
                final_title = final_title[:-1]
            
            with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
                json.dump({"title": final_title, "raw": result}, f, ensure_ascii=False)
            log(f"[2] ✅ 最终标题: {final_title}")
            return final_title
    
    log("[2] DeepSeek失败，使用模板")
    topic = items[0]["title"] if items else "健康养生"
    final_title = f"医生不会告诉你的{topic}真相"
    while len(final_title.encode('utf-8')) > 60:
        final_title = final_title[:-1]
    
    with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
        json.dump({"title": final_title, "source": "template"}, f, ensure_ascii=False)
    log(f"[2] 备用标题: {final_title}")
    return final_title

def node3_outline():
    """生成大纲 - 使用三把钩子法"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title_data = json.load(f)
            title = title_data["title"]
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            source = json.load(f)["items"][0].get("source", "网络")
    except:
        title = "健康养生文章"
        source = "网络"
    
    log("[3] 使用三把钩子法生成大纲...")
    
    prompt = THREE_HOOKS_OUTLINE_PROMPT.format(title=title, source=source)
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, temperature=0.7)
    
    if result:
        log(f"[3] 大纲生成成功，长度: {len(result)}字")
        with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
            json.dump({"outline": result, "title": title}, f, ensure_ascii=False)
        return result
    
    log("[3] DeepSeek失败，使用模板")
    outline = f"""【目标读者】
- 人群：50-70岁中老年人
- 痛点：担心健康、不知道怎么养生
- 收获：科学养生方法

【核心金句】
健康是最宝贵的财富，预防大于治疗。

【文章结构】
- 引言：从{source}热榜话题引入
- 第一部分：问题现状
- 第二部分：科学解读
- 第三部分：实用建议
- 结尾：总结+互动问题"""
    
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump({"outline": outline, "title": title}, f, ensure_ascii=False)
    return outline

def node4_article():
    """生成正文 - 使用三把钩子写作法"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/outline.json", encoding="utf-8") as f:
            outline_data = json.load(f)
            outline = outline_data.get("outline", "")
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            source = json.load(f)["items"][0].get("source", "网络")
    except:
        title = "健康养生文章"
        outline = ""
        source = "网络"
    
    log("[4] 使用三把钩子写作法生成正文...")
    
    prompt = THREE_HOOKS_ARTICLE_PROMPT.format(title=title, outline=outline[:2000] if outline else "基础大纲")
    result = call_deepseek(prompt, THREE_HOOKS_SYSTEM, temperature=0.8)
    
    if result:
        article = result
        log(f"[4] 正文生成成功: {len(article)}字")
    else:
        log("[4] DeepSeek失败，使用模板")
        article = f"""【{title}】

最近在{source}上看到这个话题，今天来和大家聊聊。

■ 引言
随着生活水平的提高，越来越多的人开始关注健康养生问题。

■ 问题现状
调查显示，超过60%的中老年人存在健康误区。

■ 科学解读
健康养生需要科学方法，预防大于治疗。

■ 实用建议
1. 规律作息：早睡早起，保证7-8小时睡眠
2. 合理膳食：少油少盐，多吃蔬菜水果
3. 适度运动：每天30分钟中等强度运动
4. 定期体检：每年至少一次全面体检
5. 心态平和：保持乐观积极的生活态度

■ 结语
健康是最宝贵的财富。希望今天的分享对大家有帮助！

——
*本文由AI自动生成 | 数据来源：{source}热榜*"""

    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({"title": title, "article": article, "source": source}, f, ensure_ascii=False)
    log(f"[4] 正文完成: {len(article)}字")
    return article

def node5_summary():
    """生成摘要"""
    try:
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            data = json.load(f)
        summary = data["article"][:200] + "..."
    except:
        summary = "健康养生文章..."
    with open(f"{DATA_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary}, f, ensure_ascii=False)
    log("[5] 摘要完成")
    return summary

def node6_send():
    """发送内容"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            article_data = json.load(f)
            article = article_data["article"]
            source = article_data.get("source", "网络")
        
        result = send_to_wechat(
            title=f"📝 新文章：{title}",
            content=f"📊 **来源：** {source}热榜\n\n🏷️ **标题：** {title}\n\n📄 **正文：**\n{article}\n\n━━━━━━━━━━━━━━━\n👆 以上是今日生成的文章内容\n请复制到公众号后台发布"
        )
        
        if result.get("code") == 0:
            log("[6] ✅ 发送成功！")
            return {"status": "success", "message": "已发送到微信"}
        else:
            log(f"[6] ❌ 发送失败: {result}")
            return {"status": "failed", "error": result}
    except Exception as e:
        log(f"[6] 异常: {e}")
        return {"status": "error", "error": str(e)}

@app.route("/")
def index():
    return "✅ 内容生产流水线<br>三源热榜 + 三把钩子写作法<br>DeepSeek生成爆款文章"

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
        node5_summary()
        result = node6_send()
        
        log("="*50)
        log("🏁 流水线完成")
        log("="*50)
        
        return jsonify({"success": True, "result": result})
    except Exception as e:
        log(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route("/test")
def test():
    result = send_to_wechat(
        title="🧪 测试消息",
        content="测试消息\n\n三源热榜 + 三把钩子写作法已就绪！"
    )
    return jsonify({"success": True, "result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
