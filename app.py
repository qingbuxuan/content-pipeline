from flask import Flask, jsonify
import os
import json
import base64
from datetime import datetime
import requests

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))
DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

def node6_publish():
    appid = os.environ.get("WECHAT_APPID", "")
    secret = os.environ.get("WECHAT_SECRET", "")

    if not appid or not secret:
        log("[6] 未配置公众号，跳过")
        return {"status": "skipped"}

    try:
        # 获取token
        token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        token_resp = requests.get(token_url, timeout=10).json()
        log(f"[6] token响应: {token_resp}")
        token = token_resp.get("access_token")

        if not token:
            return {"status": "failed", "error": f"token失败: {token_resp}"}

        log("[6] token成功!")

        # 上传封面图（临时素材）
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAYAAAB5fY51AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH6AQDCgcKpMuGIgAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAFklEQVR42mNk+M9Qz0AEYBxVQF8BAARuAAFMBSZRAAAAAElFTkSuQmCC"
        )
        upload_url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type=image"
        files = {"media": ("cover.png", png_data, "image/png")}
        media_resp = requests.post(upload_url, files=files, timeout=30).json()
        log(f"[6] 封面上传: {media_resp}")
        thumb_media_id = media_resp.get("media_id")

        if not thumb_media_id:
            return {"status": "failed", "error": f"封面上传失败: {media_resp}"}

        # 使用 add_news 接口（订阅号支持）
        news_url = f"https://api.weixin.qq.com/cgi-bin/material/add_news?access_token={token}"
        payload = {
            "articles": [
                {
                    "title": "健康养生",
                    "thumb_media_id": thumb_media_id,
                    "author": "AI",
                    "digest": "健康养生知识分享",
                    "show_cover_pic": 1,
                    "content": "<p>健康养生，从今天开始。</p>",
                    "content_source_url": ""
                }
            ]
        }

        resp = requests.post(news_url, json=payload, timeout=30).json()
        log(f"[6] add_news结果: {resp}")

        if "media_id" in resp:
            log("[6] ✅ 发布成功！")
            return {"status": "success", "media_id": resp["media_id"]}
        else:
            return {"status": "failed", "error": str(resp)}

    except Exception as e:
        log(f"[6] 异常: {e}")
        return {"status": "error", "error": str(e)}

@app.route("/")
def index():
    return "服务运行正常"

@app.route("/trigger")
def trigger():
    log("="*40)
    log("流水线启动")
    log("="*40)
    result = node6_publish()
    log("="*40)
    log("流水线完成")
    log("="*40)
    return jsonify({"success": True, "result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
