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

def call_deepseek(prompt, system_prompt="你是一个有用的助手"):
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
            "temperature": 0.8,
            "max_tokens": 500
        }
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
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
    """生成标题 - 使用 DeepSeek"""
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            items = json.load(f)["items"]
        hot_topics = "\n".join([f"- {item['title']} (来源:{item['source']})" for item in items])
    except:
        hot_topics = "中老年人如何科学养生？\n老年人睡眠不好怎么办？\n退休后如何保持身心健康"
        items = [{"title": "中老年人如何科学养生？", "source": "默认"}]
    
    log("[2] 使用DeepSeek生成标题...")
    
    # DeepSeek 提示词
    system_prompt = """你是一位超厉害的微信公众号爆款标题制造大师，拥有深厚的文字功底和敏锐的热点洞察力。擅长创作吸引眼球的标题。"""
    
    user_prompt = f"""## 任务
从以下热榜话题中，筛选出与"中年、中老年健康养生、养老、情感"相关的内容，生成5个微信公众号爆款标题。

## 热榜话题
{hot_topics}

## 要求
1. 标题要符合微信公众号风格
2. 具有吸引力，能抓住读者眼球
3. 可以结合多个话题或延伸话题
4. 最终输出最优的一个标题

## 输出格式
先列出5个候选标题，然后标注"最终标题："后面跟最优的那个

注意：最终标题不要超过30个中文字符！"""

    # 调用 DeepSeek
    result = call_deepseek(user_prompt, system_prompt)
    
    if result:
        log(f"[2] DeepSeek返回:\n{result}")
        
        # 提取最终标题
        lines = result.split("\n")
        final_title = None
        for line in lines:
            if "最终标题" in line or "【最终】" in line or "★" in line:
                # 提取标题
                title = line.split("：")[-1].split("】")[-1].strip()
                if title and len(title) <= 35:
                    final_title = title
                    break
        
        # 如果没找到最终标题标记，取最后一行
        if not final_title:
            for line in reversed(lines):
                line = line.strip()
                if line and len(line) > 5:
                    final_title = line.strip("★※【】\"\"''")
                    if len(final_title) <= 35:
                        break
        
        if final_title:
            # 确保不超过64字节
            while len(final_title.encode('utf-8')) > 60 and len(final_title) > 10:
                final_title = final_title[:-1]
            
            with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
                json.dump({"title": final_title, "raw": result}, f, ensure_ascii=False)
            log(f"[2] ✅ 最终标题: {final_title}")
            return final_title
    
    # 备用方案：模板生成
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
    """生成大纲"""
    outline = "引言 → 问题现状 → 科学解读 → 实用建议 → 注意事项 → 结语"
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump({"outline": outline}, f, ensure_ascii=False)
    log("[3] 大纲完成")
    return outline

def node4_article():
    """生成正文"""
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            source = json.load(f)["items"][0].get("source", "网络")
    except:
        title = "健康养生文章"
        source = "网络"
    
    article = f"""【{title}】

最近在{source}上看到这个话题，今天来和大家聊聊。

■ 引言
随着生活水平的提高，越来越多的人开始关注健康养生问题。但网上信息鱼龙混杂，到底哪些是真哪些是假？

■ 问题现状
调查显示，超过60%的中老年人存在健康误区：
- 盲目购买保健品
- 道听途说跟风养生
- 忽视定期体检

■ 科学解读
专家表示，健康养生需要科学方法：
1. 每个人体质不同，养生方式也要因人而异
2. 没有"万能保健品"，健康需要综合管理
3. 预防大于治疗，定期体检是关键

■ 实用建议
1. 规律作息：早睡早起，保证7-8小时睡眠
2. 合理膳食：少油少盐，多吃蔬菜水果
3. 适度运动：每天30分钟中等强度运动
4. 定期体检：每年至少一次全面体检
5. 心态平和：保持乐观积极的生活态度

■ 注意事项
- 不要盲目购买三无保健品
- 有身体不适及时就医
- 科学养生才是正道

■ 结语
健康是最宝贵的财富。希望今天的分享对大家有帮助！

——
*本文由AI自动生成 | 数据来源：{source}热榜
可直接复制到公众号发布*
"""

    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({"title": title, "article": article, "source": source}, f, ensure_ascii=False)
    log(f"[4] 正文生成: {len(article)}字 | 来源: {source}")
    return article

def node5_summary():
    """生成摘要"""
    try:
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            data = json.load(f)
        summary = data["article"][:150] + "..."
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
            content=f"**来源：** {source}热榜\n\n**标题：** {title}\n\n**正文：**\n{article}\n\n━━━━━━━━━━━━━━━\n👆 以上是今日生成的文章内容\n请复制到公众号后台发布"
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
    return "✅ 内容生产流水线<br>三源热榜 + DeepSeek标题生成<br>每天自动推送到微信"

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
        content="这是一条测试消息，如果收到这条消息，说明推送功能正常！\n\n三源热榜 + DeepSeek标题已就绪！"
    )
    return jsonify({"success": True, "result": result})

@app.route("/test_deepseek")
def test_deepseek():
    """测试 DeepSeek API"""
    log("[测试] 调用DeepSeek...")
    result = call_deepseek("请生成一个关于健康养生的微信公众号标题，20字以内")
    if result:
        return jsonify({"success": True, "result": result})
    else:
        return jsonify({"success": False, "error": "API调用失败"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
