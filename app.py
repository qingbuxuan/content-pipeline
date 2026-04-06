"""
微信公众号草稿箱测试文件
功能：上传封面图 → 创建草稿箱文章

使用方式：
1. 在 Render 环境变量中配置：WX_APPID, WX_APPSECRET
2. 访问 /test_draft 触发测试
3. 测试成功后，可合并到主流程 node6
"""

from flask import Flask, jsonify, request
import os
import json
import requests
from datetime import datetime

app = Flask(__name__)
DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Server酱配置（备用推送）
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "SCT333499TpvZQWzbvJcMfDxo7BmL8MsrV")

# 微信公众平台配置（从环境变量读取）
WX_APPID = os.environ.get("WX_APPID", "")
WX_APPSECRET = os.environ.get("WX_APPSECRET", "")

# 通义万相配置（生成封面图）
WANXIANG_API_KEY = os.environ.get("WANXIANG_API_KEY", "sk-de7984bb01c84a2bb136167006864fe2")

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

# ========== 微信 API 核心函数 ==========

def get_access_token():
    """获取 Access Token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": WX_APPID, "secret": WX_APPSECRET}
    resp = requests.get(url, params=params, timeout=10)
    result = resp.json()
    
    if "access_token" in result:
        log(f"[微信] Access Token 获取成功: {result['access_token'][:20]}...")
        return result["access_token"]
    else:
        log(f"[微信] Access Token 获取失败: {result}")
        return None

def upload_permanent_image(access_token, image_url):
    """下载封面图并上传为永久素材，返回 media_id"""
    log(f"[微信] 下载封面图: {image_url}")
    
    # 1. 下载图片
    img_resp = requests.get(image_url, timeout=30)
    if img_resp.status_code != 200:
        log(f"[微信] 图片下载失败: HTTP {img_resp.status_code}")
        return None
    
    image_bytes = img_resp.content
    log(f"[微信] 图片下载成功: {len(image_bytes)} bytes")
    
    # 2. 上传为永久素材（图片）
    upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material"
    files = {"media": ("cover.png", image_bytes, "image/png")}
    data = {"access_token": access_token, "type": "image"}
    
    upload_resp = requests.post(upload_url, params=data, files=files, timeout=30)
    upload_result = upload_resp.json()
    
    log(f"[微信] 上传素材结果: {upload_result}")
    
    if "media_id" in upload_result:
        media_id = upload_result["media_id"]
        log(f"[微信] 永久素材 media_id: {media_id}")
        return media_id
    else:
        log(f"[微信] 素材上传失败: {upload_result}")
        return None

def upload_thumb_image(access_token, image_url):
    """下载封面图 → 压缩到64KB内 → 上传为缩略图，返回 media_id"""
    log(f"[微信] 下载并压缩封面图: {image_url}")
    
    # 1. 下载图片
    img_resp = requests.get(image_url, timeout=30)
    if img_resp.status_code != 200:
        log(f"[微信] 图片下载失败: HTTP {img_resp.status_code}")
        return None
    
    original_bytes = img_resp.content
    log(f"[微信] 原始图片大小: {len(original_bytes) / 1024:.1f} KB")
    
    # 2. 用 Pillow 压缩图片（微信 thumb 限制 64KB）
    try:
        import io
        from PIL import Image
    except ImportError as e:
        log(f"[微信] Pillow 未安装: {e}")
        return None
    
    try:
        img = Image.open(io.BytesIO(original_bytes))
        log(f"[微信] 原始尺寸: {img.width}x{img.height}, 模式: {img.mode}")
    except Exception as e:
        log(f"[微信] Pillow 打开图片失败: {e}")
        return None
    
    # 转换为 RGB（处理 RGBA/PNG 透明通道）
    try:
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
    except Exception as e:
        log(f"[微信] 图片模式转换失败: {e}")
        return None
    
    # 逐步压缩直到 < 64KB
    MAX_SIZE_KB = 60  # 留点余量
    output = io.BytesIO()
    
    # 16:9 尺寸序列（从大到小）
    # 1280x720 → 900x506 → 640x360 → 480x270 → 320x180 → 240x135
    size_sequence = [
        (900, 506), (640, 360), (480, 270), (320, 180), (240, 135)
    ]
    
    best_bytes = None
    compressed = None
    
    for tgt_w, tgt_h in size_sequence:
        # 按目标尺寸缩放（只缩小，不放大）
        w, h = img.width, img.height
        if w > tgt_w:
            ratio = tgt_w / w
            tgt_h_calc = int(h * ratio)
            resize_img = img.resize((tgt_w, tgt_h_calc), Image.LANCZOS)
            log(f"[微信] 缩放至 {tgt_w}x{tgt_h_calc} (16:9)")
        else:
            resize_img = img
            log(f"[微信] 使用原始尺寸 {w}x{h}")
        
        # 在当前尺寸下，逐步降低 JPEG 质量
        for quality in [80, 60, 40, 25, 15, 10]:
            try:
                output.seek(0)
                output.truncate()
                resize_img.save(output, format="JPEG", quality=quality, optimize=True)
                compressed = output.getvalue()
                size_kb = len(compressed) / 1024
                log(f"[微信] 质量={quality}, 大小={size_kb:.1f}KB {'✅' if size_kb < MAX_SIZE_KB else '❌'}")
                
                if size_kb < MAX_SIZE_KB:
                    best_bytes = compressed
                    log(f"[微信] ✅ 压缩达标: {resize_img.width}x{resize_img.height} @ q={quality}, {size_kb:.1f}KB")
                    break
            except Exception as e:
                log(f"[微信] 压缩异常 quality={quality}: {e}")
        
        if best_bytes:
            break
    
    if best_bytes is None and compressed:
        log("[微信] ⚠️ 未达64KB限制，使用最小尺寸尝试上传")
        best_bytes = compressed
    elif best_bytes is None:
        log("[微信] ❌ 压缩完全失败")
        return None
    
    log(f"[微信] 最终压缩大小: {len(best_bytes)/1024:.1f}KB")
    
    # 3. 上传为 thumb 类型
    upload_url = f"https://api.weixin.qq.com/cgi-bin/media/upload"
    files = {"media": ("cover.jpg", best_bytes, "image/jpeg")}
    data = {"access_token": access_token, "type": "thumb"}
    
    upload_resp = requests.post(upload_url, params=data, files=files, timeout=30)
    upload_result = upload_resp.json()
    
    log(f"[微信] 缩略图上传结果: {upload_result}")
    
    if "thumb_media_id" in upload_result:
        thumb_media_id = upload_result["thumb_media_id"]
        log(f"[微信] thumb_media_id: {thumb_media_id}")
        return thumb_media_id
    else:
        log(f"[微信] 缩略图上传失败: {upload_result}")
        return None

def create_draft(access_token, title, author, digest, content_html, thumb_media_id):
    """创建草稿箱文章"""
    log(f"[微信] 创建草稿箱文章...")
    
    # 转换内容为 HTML 片段（微信草稿箱格式）
    content_body = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content_html,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    
    articles = [{"thumb_media_id": thumb_media_id, "author": author, "title": title, 
                 "content_source_url": "", "digest": digest, "content": content_html,
                 "thumb_url": ""}]
    
    payload = {"articles": articles}
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add"
    params = {"access_token": access_token}
    headers = {"Content-Type": "application/json; charset=utf-8"}
    
    resp = requests.post(url, params=params, json=payload, headers=headers, timeout=15)
    result = resp.json()
    
    log(f"[微信] 创建草稿结果: {result}")
    
    if result.get("errcode") == 0:
        log(f"[微信] ✅ 草稿创建成功！")
        return True
    else:
        log(f"[微信] ❌ 草稿创建失败: {result}")
        return False

# ========== 通义万相生成封面图 ==========

def generate_cover_image(prompt):
    """调用通义万相生成封面图"""
    try:
        log(f"[封面] 生成封面图...")
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WANXIANG_API_KEY}",
            "X-DashScope-Async": "enable"
        }
        payload = {
            "model": "wanx-v1",
            "input": {"prompt": prompt},
            "parameters": {"style": "<auto>", "size": "1280*720", "n": 1}
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        result = resp.json()
        log(f"[封面] 任务创建: {result}")
        
        if "output" in result and "task_id" in result["output"]:
            task_id = result["output"]["task_id"]
            
            # 轮询等待结果（最多30次，每次3秒）
            for i in range(30):
                import time
                time.sleep(3)
                
                status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
                status_resp = requests.get(status_url, headers={"Authorization": f"Bearer {WANXIANG_API_KEY}"})
                status_result = status_resp.json()
                
                task_status = status_result.get("output", {}).get("task_status", "")
                log(f"[封面] 状态: {task_status}")
                
                if task_status == "SUCCEEDED":
                    results = status_result.get("output", {}).get("results", [])
                    if results:
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

# ========== ServerChan 备用推送 ==========

def send_to_wechat(title, content):
    """通过 Server酱 发送微信通知（备用）"""
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        data = {"title": title, "desp": content}
        resp = requests.post(url, data=data, timeout=10)
        result = resp.json()
        log(f"[备用] 发送结果: {result}")
        return result
    except Exception as e:
        log(f"[备用] 发送失败: {e}")
        return {"code": -1, "msg": str(e)}

# ========== 测试用示例文章 ==========

TEST_ARTICLE = {
    "title": "测试文章：子女不在身边，老人如何告别孤独感？",
    "author": "健康养生",
    "digest": "子女不在身边，空巢老人的孤独感如何化解？这三个方法值得尝试。",
    "content": """<p>李阿姨今年68岁，退休前是小学老师。老伴三年前走了，儿子在上海工作，一年回来两三次。</p>

<p>她说，最难熬的不是夜里醒来的那两个小时，而是白天。手机里儿子的照片看了又看，想打电话又怕打扰他工作。邻居叫她去跳舞，她说不爱动。其实不是不爱动，是不想一个人出门。</p>

<p>这是很多空巢老人的真实写照。</p>

<p>孤独感对老年人的伤害，比我们想象的大得多。研究表明，长期孤独会增加患心血管疾病、抑郁症的风险，严重的甚至影响寿命。</p>

<p>那怎么办？</p>

<p>第一，给自己找个"寄托"。养花、养鸟、养猫狗都行，重要的是有个活物等着你回家。我认识一位王大爷，退休后迷上了养鸟，每天早上五点起来喂鸟，现在精神头比退休前还好。</p>

<p>第二，主动走出去，别等别人来找你。小区里的广场舞队、棋牌室、社区老年大学，都是好去处。别觉得自己格格不入，大家都是来找伴儿的，谁也别笑话谁。</p>

<p>第三，学会用手机和儿女"见面"。微信视频比打电话强多了，能看见脸的距离感，比听到声音的孤独感要小很多。不会用？让儿女教，教不会就多打几遍电话，厚着脸皮问。</p>

<p>其实啊，子女也要主动。哪怕每天一条微信、一个短视频，比每个月打一次电话强。父母不图你有钱，就图你知道惦记他们。</p>

<p>老有所依，不是物质上的依靠，是心里的那份牵挂。</p>""",
    "cover_prompt": "An elderly Chinese woman sitting by the window, looking out at a quiet neighborhood, warm afternoon sunlight, gentle and peaceful atmosphere, realistic photography style, 16:9"
}

# ========== 草稿箱推送主函数 ==========

def push_to_draft():
    """草稿箱推送完整流程"""
    log("=" * 50)
    log("🚀 草稿箱测试启动")
    log("=" * 50)
    
    # 检查凭证
    if not WX_APPID or not WX_APPSECRET:
        log("❌ 缺少 WX_APPID 或 WX_APPSECRET 环境变量")
        return {"status": "error", "message": "缺少微信公众号凭证"}
    
    # 1. 生成封面图
    log("[1] 生成封面图...")
    cover_url = generate_cover_image(TEST_ARTICLE["cover_prompt"])
    if not cover_url:
        log("❌ 封面图生成失败，终止")
        return {"status": "error", "message": "封面图生成失败"}
    
    # 2. 获取 Access Token
    log("[2] 获取 Access Token...")
    access_token = get_access_token()
    if not access_token:
        log("❌ Access Token 获取失败，终止")
        return {"status": "error", "message": "Access Token 获取失败"}
    
    # 3. 上传缩略图
    log("[3] 上传缩略图...")
    thumb_media_id = upload_thumb_image(access_token, cover_url)
    if not thumb_media_id:
        log("❌ 缩略图上传失败，终止")
        return {"status": "error", "message": "缩略图上传失败"}
    
    # 4. 创建草稿
    log("[4] 创建草稿箱...")
    success = create_draft(
        access_token,
        title=TEST_ARTICLE["title"],
        author=TEST_ARTICLE["author"],
        digest=TEST_ARTICLE["digest"],
        content_html=TEST_ARTICLE["content"],
        thumb_media_id=thumb_media_id
    )
    
    if success:
        log("=" * 50)
        log("✅ 草稿箱推送成功！请到公众号后台查看草稿箱")
        log("=" * 50)
        
        # 同时 ServerChan 通知
        notify_content = f"""✅ 草稿箱推送成功！

📌 文章标题：{TEST_ARTICLE['title']}
📷 封面图：{cover_url}

请到 公众号后台 → 内容与互动 → 草稿箱 查看并发布。"""
        
        send_to_wechat("📝 草稿箱推送成功", notify_content)
        
        return {"status": "success", "cover_url": cover_url, "message": "草稿箱推送成功"}
    else:
        log("=" * 50)
        log("❌ 草稿箱推送失败！")
        log("=" * 50)
        return {"status": "failed", "message": "草稿箱推送失败"}

# ========== Flask 路由 ==========

@app.route("/")
def index():
    return """✅ 草稿箱测试服务运行中

路由说明：
• GET /test_draft → 触发草稿箱测试（使用测试文章）
• GET /test_status → 检查配置状态
• GET /push_draft?title=xxx → 推送指定文章到草稿箱
"""

@app.route("/test_status")
def test_status():
    """检查环境变量配置状态"""
    return jsonify({
        "WX_APPID": "✅ 已配置" if WX_APPID else "❌ 未配置",
        "WX_APPSECRET": "✅ 已配置" if WX_APPSECRET else "❌ 未配置",
        "SERVERCHAN_KEY": "✅ 已配置" if SERVERCHAN_KEY else "❌ 未配置",
        "WANXIANG_API_KEY": "✅ 已配置" if WANXIANG_API_KEY else "❌ 未配置",
    })

@app.route("/test_draft")
def test_draft():
    """触发草稿箱测试"""
    result = push_to_draft()
    
    if result["status"] == "success":
        return jsonify({"success": True, "result": result})
    elif result["status"] == "error":
        return jsonify({"success": False, "error": result["message"]}), 500
    else:
        return jsonify({"success": False, "error": result["message"]}), 500

@app.route("/push_draft")
def push_draft_route():
    """推送指定文章到草稿箱（用于正式流程）"""
    title = request.args.get("title", "测试标题")
    author = request.args.get("author", "")
    digest = request.args.get("digest", "")
    content = request.args.get("content", "<p>测试内容</p>")
    cover_url = request.args.get("cover_url", "")
    
    if not cover_url:
        return jsonify({"success": False, "error": "缺少 cover_url 参数"}), 400
    
    # 获取 Access Token
    access_token = get_access_token()
    if not access_token:
        return jsonify({"success": False, "error": "Access Token 获取失败"}), 500
    
    # 上传缩略图
    thumb_media_id = upload_thumb_image(access_token, cover_url)
    if not thumb_media_id:
        return jsonify({"success": False, "error": "缩略图上传失败"}), 500
    
    # 创建草稿
    success = create_draft(access_token, title, author, digest, content, thumb_media_id)
    
    if success:
        send_to_wechat(f"✅ 草稿推送成功：{title}", f"文章已推送至草稿箱，请及时发布。\n封面：{cover_url}")
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "草稿创建失败"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
