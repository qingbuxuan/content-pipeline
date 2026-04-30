# -*- coding: utf-8 -*-
"""微信 API：AccessToken、封面图上传、草稿箱图文"""
from config import *
from utils import *

def get_access_token():
    if not WX_APPID or not WX_APPSECRET:
        log("[微信] 缺少 WX_APPID 或 WX_APPSECRET，跳过草稿箱推送")
        return None
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": WX_APPID, "secret": WX_APPSECRET}
    resp = requests.get(url, params=params, timeout=10)
    result = resp.json()
    if "access_token" in result:
        log(f"[微信] Access Token: {result['access_token'][:20]}...")
        return result["access_token"]
    log(f"[微信] Access Token 获取失败: {result}")
    return None

def upload_cover_for_draft(access_token, image_url):
    log(f"[微信] 下载封面图: {image_url}")
    if image_url.startswith("data:"):
        log("[微信] 本地图片降级方案")
        match = re.match(r"data:image/\w+;base64,(.+)", image_url)
        if match:
            original_bytes = base64.b64decode(match.group(1))
        else:
            log("[微信] Base64 格式解析失败")
            return None
    else:
        img_resp = requests.get(image_url, timeout=30)
        if img_resp.status_code != 200:
            log(f"[微信] 图片下载失败: HTTP {img_resp.status_code}")
            return None
        original_bytes = img_resp.content
    log(f"[微信] 原始: {len(original_bytes)/1024:.1f} KB")
    try:
        img = Image.open(io.BytesIO(original_bytes))
        log(f"[微信] 尺寸: {img.width}x{img.height}, 模式: {img.mode}")
    except Exception as e:
        log(f"[微信] Pillow 打开失败: {e}")
        return None
    if img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    tgt_w = 900
    if img.width > tgt_w:
        ratio = tgt_w / img.width
        img = img.resize((tgt_w, int(img.height * ratio)), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85, optimize=True)
    compressed = output.getvalue()
    log(f"[微信] 压缩后: {len(compressed)/1024:.1f} KB")
    upload_url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    files = {"media": ("cover.jpg", compressed, "image/jpeg")}
    data = {"access_token": access_token, "type": "image"}
    upload_resp = requests.post(upload_url, params=data, files=files, timeout=30)
    upload_result = upload_resp.json()
    log(f"[微信] 上传结果: {upload_result}")
    if "media_id" in upload_result:
        media_id = upload_result["media_id"]
        thumb_url = upload_result.get("url", "")
        log(f"[微信] media_id: {media_id}")
        return {"media_id": media_id, "url": thumb_url}
    log(f"[微信] 上传失败: {upload_result}")
    return None

def create_draft(access_token, title, author, digest, content_html, media_id, thumb_url=""):
    log(f"[微信] 创建草稿箱文章...")
    title_utf8 = len(title.encode("utf-8"))
    log(f"[微信] 标题: '{title}' ({len(title)}字, {title_utf8}B)")
    
    # 如果标题超长，使用智能截断（优先在标点处断开）
    if title_utf8 > 64:
        # 在 node2_title 已经限制在 60B 内，这里是双重保险
        title = truncate_title_smart(title, 64)
        log(f"[微信] 标题智能截断: '{title}' ({len(title.encode('utf-8'))}B)")
    payload = {"articles": [{"title": title, "author": author, "digest": digest, "content": content_html,
                              "content_source_url": "", "thumb_media_id": media_id, "thumb_url": thumb_url}]}
    url = "https://api.weixin.qq.com/cgi-bin/draft/add"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    json_body = json.dumps(payload, ensure_ascii=False)
    resp = requests.post(url, params={"access_token": access_token}, data=json_body.encode("utf-8"),
                         headers=headers, timeout=15)
    result = resp.json()
    log(f"[微信] 创建结果: {result}")
    if result.get("errcode") == 0 or "media_id" in result:
        log("[微信] 草稿创建成功！")
        return True
    log(f"[微信] 草稿创建失败: {result}")
    return False

def push_article_to_draft(title, author, digest, content_html, cover_url, weekday):
    access_token = get_access_token()
    if not access_token:
        return False
    media_result = upload_cover_for_draft(access_token, cover_url)
    if not media_result:
        return False
    return create_draft(access_token, title, author, digest, content_html,
                         media_result["media_id"], media_result.get("url", ""))
