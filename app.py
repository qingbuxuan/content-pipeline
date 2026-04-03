# 内容生产流水线 - Render 部署版

from flask import Flask, jsonify
import os
import json
import base64
from datetime import datetime
import requests

app = Flask(__name__)

DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

def truncate_title(title, max_bytes=64):
"""按字节截断标题，确保最终字节数不超过 max_bytes"""
    title_bytes = title.encode('utf-8')
    if len(title_bytes) <= max_bytes:
        return title

    # 逐字符累积，为省略号预留 3 字节空间
    result = ""
    for ch in title:
        test = result + ch
        if len(test.encode('utf-8')) <= max_bytes - 3:
            result = test
        else:
            # 剩余空间不足以再加一个字符，尝试添加省略号
            if len(result.encode('utf-8')) + 3 <= max_bytes:
                result += "..."
            break
    return result

def truncate_str(s, max_bytes=20):
    """截断字符串（用于作者名等）"""
    if not s:
        return s
    if len(s.encode('utf-8')) <= max_bytes:
        return s
    result = ""
    for char in s:
        test = result + char
        if len(test.encode('utf-8')) > max_bytes - 2:
            result += ".."
            break
        result += char
    return result

def node1_collector():
    keywords = ["健康", "养生", "中医", "运动", "睡眠", "心理", "情感", "家庭", "婚姻", "父母", "养老", "中年", "老年", "血压", "血糖"]
    items = []
    try:
        r = requests.get("https://top.baidu.com/api/board/getBoard?boardId=realtime", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        items += [{"title": i["query"], "source": "百度"} for i in r.json()["data"]["content"][:20]]
    except:
        pass
    try:
        r = requests.get("https://weibo.com/ajax/side/hotSearch", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        items += [{"title": i["word"], "source": "微博"} for i in r.json()["data"]["realtime"][:20]]
    except:
        pass
    
    if not items:
        items = [
            {"title": "中老年人如何科学养生？医生给出5条建议", "source": "mock"},
            {"title": "老年人睡眠不好怎么办？专家支招", "source": "mock"},
            {"title": "退休后如何保持身心健康", "source": "mock"},
            {"title": "中年人必看：预防高血压的日常方法", "source": "mock"},
            {"title": "中医养生：四季饮食调理指南", "source": "mock"},
        ]
        log("API不可用，使用模拟数据")
    
    for item in items:
        item["score"] = sum(2 if kw in ["健康", "养生", "情感"] else 1 for kw in keywords if kw in item["title"])
    filtered = sorted([i for i in items if i["score"] > 0], key=lambda x: x["score"], reverse=True)[:10]
    
    with open(f"{DATA_DIR}/candidates.json", "w") as f:
        json.dump({"date": str(datetime.now().date()), "items": filtered}, f)
    
    log(f"[1] 采集完成: {len(filtered)}条")
    return filtered

def node2_title():
    try:
        with open(f"{DATA_DIR}/candidates.json") as f:
            items = json.load(f)["items"]
        title = items[0]["title"] if items else "健康养生文章"
    except:
        title = "健康养生文章"
    
    best_title = f"医生不会告诉你的{title.split('？')[0]}真相"
    best_title = truncate_title(best_title, 50)
    with open(f"{DATA_DIR}/title.json", "w") as f:
        json.dump({"title": best_title}, f)
    log(f"[2] 标题: {best_title} ({len(best_title.encode('utf-8'))}字节)")
    return best_title

def node3_outline():
    try:
        with open(f"{DATA_DIR}/title.json") as f:
            title = json.load(f)["title"]
    except:
        title = "健康养生文章"
    outline = {"title": title, "sections": ["引言", "问题现状", "科学解读", "实用建议", "注意事项", "结语"]}
    with open(f"{DATA_DIR}/outline.json", "w") as f:
        json.dump(outline, f)
    log("[3] 大纲完成")
    return outline

def node4_article():
    try:
        with open(f"{DATA_DIR}/outline.json") as f:
            title = json.load(f)["title"]
    except:
        title = "健康养生文章"
    
    article = f"""# {title}

## 引言
随着生活水平的提高，越来越多的中老年人开始关注健康养生问题。

## 问题现状
调查显示，超过60%的中老年人存在健康误区。

## 科学解读
从医学角度来看，人体在进入中老年阶段后，各项机能都会发生变化。

## 实用建议
1. 规律作息：保证每天7-8小时的睡眠
2. 合理饮食：少油少盐，多吃蔬菜水果
3. 适度运动：每天30分钟以上中等强度运动
4. 定期体检：每年至少一次全面体检
5. 心态平和：保持乐观积极的心态

## 注意事项
- 不要盲目跟风
- 出现不适及时就医
- 用药遵医嘱

## 结语
健康是最宝贵的财富。希望今天的分享能帮助大家。

---
*本文由AI助手生成*
"""
    
    with open(f"{DATA_DIR}/article.json", "w") as f:
        json.dump({"title": title, "article": article, "word_count": len(article)}, f)
    log(f"[4] 正文: {len(article)}字")
    return article

def node5_summary():
    try:
        with open(f"{DATA_DIR}/article.json") as f:
            data = json.load(f)
        summary = data["article"][:120] + "..."
    except:
        summary = "本文分享了健康养生知识和实用建议..."
    
    with open(f"{DATA_DIR}/summary.json", "w") as f:
        json.dump({"summary": summary}, f)
    log("[5] 摘要完成")
    return summary

def node6_publish():
    appid = os.environ.get("WECHAT_APPID", "")
    secret = os.environ.get("WECHAT_SECRET", "")
    
    log(f"[6] appid={appid[:10]}..." if appid else "[6] appid为空")
    if not appid or not secret:
        log("[6] 公众号未配置，跳过")
        return {"status": "skipped"}
    
    try:
        # 获取token
        token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        r = requests.get(token_url, timeout=10)
        token = r.json().get("access_token")
        
        if not token:
            errcode = r.json().get("errcode")
            log(f"[6] token失败: {errcode}")
            return {"status": "failed", "error": f"token: {errcode}"}
        log(f"[6] token成功!")
        
        # 上传永久封面图片
        log("[6] 上传永久封面...")
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        
        upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb"
        files = {"media": ("cover.png", png_data, "image/png")}
        r = requests.post(upload_url, files=files, timeout=30)
        upload_result = r.json()
        log(f"[6] 上传结果: {upload_result}")
        
        thumb_media_id = upload_result.get("media_id")
        
        if not thumb_media_id:
            log(f"[6] 上传失败: {upload_result}")
            return {"status": "failed", "error": "upload failed"}
        
        log(f"[6] 永久封面ID: {thumb_media_id}")
        
        # 读取文章
        try:
            with open(f"{DATA_DIR}/article.json") as f:
                data = json.load(f)
            title = truncate_title(data["title"], 54)
            article = data["article"]
            summary = truncate_summary(data["article"], 100)
        except:
            title = "健康养生文章"
            article = "内容..."
            summary = "健康养生文章"
        
        # 截断作者名（限制8字节）
        author = truncate_str("AI", 8)
        
        # 截断摘要（限制120字节）
        if len(summary.encode('utf-8')) > 120:
            summary = summary[:40] + "..."
        
        log(f"[6] 标题: {title} ({len(title.encode('utf-8'))}字节)")
        log(f"[6] 作者: {author} ({len(author.encode('utf-8'))}字节)")
        log(f"[6] 摘要: {summary} ({len(summary.encode('utf-8'))}字节)")
        
        # 创建草稿
        html = f"<div style='font-size:16px;line-height:1.8;'>{article.replace(chr(10), '<br/>')}</div>"
        draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        
        article_data = {
            "title": title,
            "author": author,
            "digest": summary,
            "content": html,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }
        
        r = requests.post(draft_url, json={"articles": [article_data]}, timeout=30)
        result = r.json()
        log(f"[6] 草稿结果: {result}")
        
        if "media_id" in result:
            log(f"[6] 发布成功!")
            return {"status": "success", "media_id": result["media_id"]}
        else:
            log(f"[6] 发布失败: {result}")
            return {"status": "failed", "error": str(result)}
            
    except Exception as e:
        log(f"[6] 异常: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

@app.route("/")
def index():
    return "内容生产流水线已启动！"

@app.route("/health")
def health():
    return "OK"

@app.route("/trigger", methods=["GET", "POST"])
def trigger():
    log("="*50)
    log("流水线启动")
    log("="*50)
    
    try:
        node1_collector()
        node2_title()
        node3_outline()
        node4_article()
        node5_summary()
        result = node6_publish()
        
        log("="*50)
        log("流水线完成")
        log("="*50)
        
        return jsonify({"success": True, "result": result})
    except Exception as e:
        log(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
