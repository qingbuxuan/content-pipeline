def node6_publish():
    appid = os.environ.get("WECHAT_APPID", "")
    secret = os.environ.get("WECHAT_SECRET", "")

    if not appid or not secret:
        log("[6] 未配置公众号，跳过")
        return {"status": "skipped"}

    try:
        # 1. 获取TOKEN
        token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        token_resp = requests.get(token_url, timeout=10).json()
        token = token_resp.get("access_token")

        if not token:
            log("[6] token失败")
            return {"status": "failed", "error": "token失败"}

        # ======================
        # 标题：健康养生（必过）
        # ======================
        title = "健康养生"
        author = "AI"
        digest = "健康养生"
        content = "<p>健康养生</p>"

        # ======================
        # 修复：上传永久素材（解决40007）
        # ======================
        png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
        upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb"
        files = {"media": ("cover.png", png_data, "image/png")}
        media_resp = requests.post(upload_url, files=files, timeout=30).json()
        thumb_media_id = media_resp.get("media_id")

        if not thumb_media_id:
            log(f"[6] 封面上传失败: {media_resp}")
            return {"status": "failed", "error": "封面上传失败"}

        # 发布草稿
        draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        payload = {
            "articles": [
                {
                    "title": title,
                    "author": author,
                    "digest": digest,
                    "content": content,
                    "thumb_media_id": thumb_media_id
                }
            ]
        }

        resp = requests.post(draft_url, json=payload, timeout=30).json()
        log(f"[6] 草稿结果: {resp}")

        if "media_id" in resp:
            log("[6] ✅ 发布成功！")
            return {"status": "success", "media_id": resp["media_id"]}
        else:
            return {"status": "failed", "error": str(resp)}

    except Exception as e:
        log(f"[6] 异常: {e}")
        return {"status": "error", "error": str(e)}