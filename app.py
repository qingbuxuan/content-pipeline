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

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

def send_to_wechat(title, content):
    """通过 Server酱 发送微信通知"""
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        data = {
            "title": title,
            "desp": content
        }
        resp = requests.post(url, data=data, timeout=10)
        result = resp.json()
        log(f"[推送] 发送结果: {result}")
        return result
    except Exception as e:
        log(f"[推送] 发送失败: {e}")
        return {"code": -1, "msg": str(e)}

def node1_collector():
    """采集热榜"""
    keywords = ["健康", "养生", "中医", "运动", "睡眠", "心理", "情感"]
    items = [
        {"title": "中老年人如何科学养生？", "score": 3},
        {"title": "老年人睡眠不好怎么办？", "score": 3},
        {"title": "退休后如何保持身心健康", "score": 2},
        {"title": "中年人必看：预防高血压", "score": 2},
        {"title": "中医养生：四季饮食调理", "score": 2},
    ]
    # 筛选最相关的
    filtered = sorted(items, key=lambda x: x["score"], reverse=True)[:3]
    with open(f"{DATA_DIR}/candidates.json", "w", encoding="utf-8") as f:
        json.dump({"items": filtered}, f, ensure_ascii=False)
    log(f"[1] 采集完成: {len(filtered)}条")
    return filtered

def node2_title():
    """生成标题"""
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            items = json.load(f)["items"]
        topic = items[0]["title"] if items else "健康养生"
    except:
        topic = "健康养生"
    
    # 固定模板 + 话题
    title = f"医生不会告诉你的{topic}真相，早知道早受益"
    # 确保不超过64字节
    title = title[:30] + "..." if len(title.encode('utf-8')) > 60 else title
    
    with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
        json.dump({"title": title}, f, ensure_ascii=False)
    log(f"[2] 标题: {title}")
    return title

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
    except:
        title = "健康养生文章"
    
    article = f"""【{title}】

■ 引言
随着生活水平的提高，越来越多的人开始关注健康养生问题。

■ 问题现状
调查显示，很多人对健康存在误区，导致越养生越伤身。

■ 科学解读
专家表示，健康养生需要科学方法，盲目跟风不可取。

■ 实用建议
1. 规律作息，早睡早起
2. 合理膳食，少油少盐
3. 适度运动，每天30分钟
4. 定期体检，预防为主
5. 心态平和，乐观向上

■ 注意事项
- 不要盲目购买保健品
- 有问题及时就医
- 科学养生才是关键

■ 结语
关注健康，从今天开始！

——
*本文由AI自动生成，可直接复制到公众号发布
"""

    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({"title": title, "article": article}, f, ensure_ascii=False)
    log(f"[4] 正文生成: {len(article)}字")
    return article

def node5_summary():
    """生成摘要"""
    try:
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            data = json.load(f)
        summary = data["article"][:100] + "..."
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
            article = json.load(f)["article"]
        
        # 发送到微信
        result = send_to_wechat(
            title=f"📝 新文章：{title}",
            content=f"**标题：** {title}\n\n**正文：**\n{article}\n\n👆 以上是今日生成的文章内容，请复制到公众号后台发布。"
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
    return "✅ 内容生产流水线 - 每天自动生成健康养生文章并推送到微信"

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
    """测试 Server酱 推送"""
    result = send_to_wechat(
        title="🧪 测试消息",
        content="这是一条测试消息，如果收到这条消息，说明推送功能正常！"
    )
    return jsonify({"success": True, "result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
