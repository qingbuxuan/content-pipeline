# 内容生产流水线 - Render 部署版

from flask import Flask, jsonify
import os
import json
import base64
from datetime import datetime
import requests
import random

app = Flask(__name__)

DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

# 预设高质量标题模板（按关键词分类）
TITLE_TEMPLATES = {
    "health": [
        "{core}？医生推荐的3个科学方法",
        "别再瞎养生！{core}的正确方式，90%的人都错了",
        "中老年人必看：{core}的5个实用建议",
        "{core}的常见误区，看完少走弯路"
    ],
    "emotion": [
        "{core}：解开中年人的情感困局",
        "90%的家庭都忽略了：{core}的相处之道",
        "{core}？学会这几点，生活更舒心"
    ],
    "general": [
        "深度解析：{core}的底层逻辑",
        "{core}，这篇文章讲透了",
        "关于{core}，你需要知道的那些事"
    ]
}

# 预设兜底标题库（避免固定标题）
BACKUP_TITLES = [
    "中老年人科学养生指南：从饮食到运动",
    "解锁健康密码：中年人的身心养护方案",
    "家庭和睦的秘诀：学会有效沟通与理解",
    "睡眠不好不用愁：中医教你调理妙招",
    "血压血糖管理：日常做好这4件事就够了"
]

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

def get_title_category(title):
    """根据标题关键词判断分类"""
    health_kw = ["健康", "养生", "血压", "血糖", "睡眠", "中医", "运动"]
    emotion_kw = ["情感", "家庭", "婚姻", "父母", "养老", "中年", "老年"]
    
    if any(kw in title for kw in health_kw):
        return "health"
    elif any(kw in title for kw in emotion_kw):
        return "emotion"
    else:
        return "general"

def extract_core_title(title):
    """智能提取标题核心内容（处理问号/句号/感叹号）"""
    # 移除各类标点，提取核心语义
    separators = ["？", "?", "。", "！", "!", "：", ":"]
    core = title
    for sep in separators:
        if sep in core:
            core = core.split(sep)[0].strip()
    # 过滤无意义前缀
    useless_prefix = ["如何", "怎么", "怎样", "为何", "为什么"]
    for prefix in useless_prefix:
        if core.startswith(prefix):
            core = core[len(prefix):].strip()
    # 确保核心内容不为空
    return core if core else title[:10]

def truncate_title(title, max_bytes=96):
    """优化版：按字节截断+语义完整（优先按词分割）"""
    title_bytes = title.encode('utf-8')
    if len(title_bytes) <= max_bytes:
        return title
    
    # 先按词分割（中文按空格/标点，英文按空格）
    words = []
    temp_word = ""
    for char in title:
        if char in [" ", "，", "。", "？", "！", ",", ".", "?", "!"]:
            if temp_word:
                words.append(temp_word)
                words.append(char)
                temp_word = ""
            else:
                words.append(char)
        else:
            temp_word += char
    if temp_word:
        words.append(temp_word)
    
    # 逐词拼接，保证语义完整
    result = ""
    for word in words:
        test = result + word
        if len(test.encode('utf-8')) > max_bytes - 3:
            # 补充省略号，确保不超字节
            result = result.strip() + "..."
            break
        result += word
    
    # 兜底：如果逐词截断失败，退回到逐字符
    if not result:
        result = ""
        for char in title:
            test = result + char
            if len(test.encode('utf-8')) > max_bytes - 3:
                result += "..."
                break
            result += char
    
    return result.strip()

def node1_collector():
    keywords = ["健康", "养生", "中医", "运动", "睡眠", "心理", "情感", "家庭", "婚姻", "父母", "养老", "中年", "老年", "血压", "血糖"]
    items = []
    try:
        r = requests.get("https://top.baidu.com/api/board/getBoard?boardId=realtime", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        items += [{"title": i["query"], "source": "百度"} for i in r.json()["data"]["content"][:20]]
    except Exception as e:
        log(f"百度API采集失败: {e}")
        pass
    try:
        r = requests.get("https://weibo.com/ajax/side/hotSearch", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        items += [{"title": i["word"], "source": "微博"} for i in r.json()["data"]["realtime"][:20]]
    except Exception as e:
        log(f"微博API采集失败: {e}")
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
    
    # 优化评分逻辑：核心关键词权重更高
    for item in items:
        score = 0
        for kw in keywords:
            if kw in item["title"]:
                # 核心健康词权重翻倍
                if kw in ["健康", "养生", "血压", "血糖", "睡眠"]:
                    score += 3
                elif kw in ["情感", "家庭", "中年", "老年"]:
                    score += 2
                else:
                    score += 1
        item["score"] = score
    
    # 筛选高评分候选（score>0），取Top10
    filtered = sorted([i for i in items if i["score"] > 0], key=lambda x: x["score"], reverse=True)[:10]
    
    with open(f"{DATA_DIR}/candidates.json", "w", encoding="utf-8") as f:
        json.dump({"date": str(datetime.now().date()), "items": filtered}, f, ensure_ascii=False)
    
    log(f"[1] 采集完成: {len(filtered)}条")
    return filtered

def node2_title():
    try:
        with open(f"{DATA_DIR}/candidates.json", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", [])
        
        # 从Top3候选中随机选一个，增加多样性
        if len(items) >= 3:
            selected = random.choice(items[:3])
        elif items:
            selected = items[0]
        else:
            # 无候选时从兜底库随机选
            core_title = random.choice(BACKUP_TITLES)
            best_title = truncate_title(core_title, 96)
            log("[2] 无候选标题，使用兜底标题")
            with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
                json.dump({"title": best_title}, f, ensure_ascii=False)
            log(f"[2] 标题: {best_title} ({len(best_title.encode('utf-8'))}字节)")
            return best_title
        
        # 提取核心标题+匹配模板
        raw_title = selected["title"]
        category = get_title_category(raw_title)
        core_title = extract_core_title(raw_title)
        # 随机选一个模板生成标题
        template = random.choice(TITLE_TEMPLATES[category])
        best_title = template.format(core=core_title)
        
        # 按平台优化截断（公众号建议96字节）
        best_title = truncate_title(best_title, 96)
        
    except Exception as e:
        log(f"[2] 标题生成失败: {e}")
        # 异常时从兜底库随机选
        best_title = truncate_title(random.choice(BACKUP_TITLES), 96)
    
    # 保存标题（指定UTF-8编码避免乱码）
    with open(f"{DATA_DIR}/title.json", "w", encoding="utf-8") as f:
        json.dump({"title": best_title}, f, ensure_ascii=False)
    
    log(f"[2] 标题: {best_title} ({len(best_title.encode('utf-8'))}字节)")
    return best_title

def node3_outline():
    try:
        with open(f"{DATA_DIR}/title.json", encoding="utf-8") as f:
            title = json.load(f)["title"]
    except:
        title = random.choice(BACKUP_TITLES)
    
    # 动态大纲：根据标题分类调整章节
    category = get_title_category(title)
    if category == "health":
        sections = ["引言", "常见误区", "科学原理", "实用方法", "注意事项", "总结建议"]
    elif category == "emotion":
        sections = ["引言", "现状分析", "核心问题", "解决思路", "真实案例", "结语"]
    else:
        sections = ["引言", "问题现状", "深度解析", "实用建议", "注意事项", "结语"]
    
    outline = {"title": title, "sections": sections}
    with open(f"{DATA_DIR}/outline.json", "w", encoding="utf-8") as f:
        json.dump(outline, f, ensure_ascii=False)
    
    log("[3] 大纲完成")
    return outline

def node4_article():
    try:
        with open(f"{DATA_DIR}/outline.json", encoding="utf-8") as f:
            data = json.load(f)
        title = data["title"]
        sections = data["sections"]
    except:
        title = random.choice(BACKUP_TITLES)
        sections = ["引言", "问题现状", "科学解读", "实用建议", "注意事项", "结语"]
    
    # 按分类生成差异化正文
    category = get_title_category(title)
    if category == "health":
        article_content = f"""# {title}

## {sections[0]}
随着人口老龄化加剧，中老年人的健康养生问题越来越受关注。然而，市面上流传的很多"养生妙招"其实并不科学，甚至可能危害健康。

## {sections[1]}
### 误区1：盲目进补
很多老人认为"补得越多越好"，过度食用保健品，反而增加身体负担。
### 误区2：拒绝所有脂肪
完全不吃脂肪会导致脂溶性维生素缺乏，影响身体正常代谢。
### 误区3：运动越剧烈越好
中老年人关节功能下降，高强度运动易导致损伤。

## {sections[2]}
从现代医学角度来看，中老年阶段的身体特点是：
- 新陈代谢速率下降15%-20%
- 器官功能逐渐衰退
- 免疫力降低，易患慢性疾病
- 骨骼密度下降，骨折风险增加

## {sections[3]}
### 饮食调理
1. 主食多样化：粗细搭配，增加膳食纤维摄入
2. 蛋白质补充：每天适量摄入鸡蛋、牛奶、豆制品
3. 控盐控糖：每日盐摄入不超过5克，添加糖不超过25克
4. 规律进餐：三餐定时定量，避免暴饮暴食

### 运动建议
1. 选择适合的运动：太极拳、散步、广场舞、哑铃操等
2. 运动频率：每周3-5次，每次30-45分钟
3. 运动强度：以微微出汗、心率不超过120次/分钟为宜

### 日常监测
1. 血压：每天固定时间测量，记录变化趋势
2. 血糖：空腹血糖控制在4.4-7.0 mmol/L
3. 体重：每周称重，保持BMI在18.5-24.0之间

## {sections[4]}
- 养生方案需个性化，根据自身健康状况调整
- 定期体检，及时发现潜在健康问题
- 避免轻信偏方，生病及时就医
- 药物需遵医嘱，不可自行增减剂量

## {sections[5]}
健康养生是一个长期过程，没有"一招鲜"的方法。只有结合科学知识和自身情况，才能真正实现健康长寿。希望本文的建议能帮助大家走出养生误区，拥抱健康生活。
"""
    elif category == "emotion":
        article_content = f"""# {title}

## {sections[0]}
中年阶段不仅是事业的黄金期，也是家庭关系的关键期。上有老下有小的生活状态，容易让中年人陷入情感和心理的双重压力。

## {sections[1]}
据调查显示，78%的中年人表示存在不同程度的家庭沟通问题：
- 与父母的代沟加深，养老观念存在分歧
- 与伴侣的交流减少，婚姻进入"平淡期"
- 与子女的沟通不畅，亲子关系紧张

## {sections[2]}
### 核心矛盾1：代际观念差异
父母的传统观念与现代生活方式的冲突，是家庭矛盾的主要来源。
### 核心矛盾2：情感需求被忽视
中年人忙于工作和照顾家人，往往忽略了自身和伴侣的情感需求。
### 核心矛盾3：压力无处释放
生活和工作的双重压力，容易导致情绪失控，影响家庭关系。

## {sections[3]}
### 沟通技巧
1. 积极倾听：耐心听完对方的想法，不打断、不反驳
2. 换位思考：站在对方的角度理解问题
3. 温和表达：用"我觉得"代替"你不对"，减少对抗性
4. 定期交流：每周安排固定时间，和家人深入沟通

### 情绪管理
1. 找到适合的解压方式：运动、阅读、旅游等
2. 学会拒绝：不勉强自己做超出能力范围的事
3. 寻求支持：和朋友倾诉，或寻求专业心理咨询

## {sections[4]}
### 案例1：张阿姨的家庭和解
张阿姨和儿媳因育儿观念不合经常争吵，后来通过定期家庭会议，互相理解对方的想法，关系逐渐缓和。

### 案例2：李叔叔的婚姻修复
李叔叔和妻子长期缺乏沟通，婚姻陷入危机，通过参加婚姻辅导，重新学会了表达爱意和理解，婚姻关系得以修复。

## {sections[5]}
家庭和睦是中年幸福的基石。学会有效沟通、理解和包容，才能化解情感困局，让家庭成为温暖的港湾。
"""
    else:
        article_content = f"""# {title}

## {sections[0]}
在快节奏的现代生活中，{extract_core_title(title)}已经成为很多人关注的重要话题。了解其背后的逻辑和方法，对提升生活质量至关重要。

## {sections[1]}
当前，关于{extract_core_title(title)}的讨论越来越多，但很多人对其认知仍存在片面性：
- 信息碎片化，难以形成系统认知
- 伪科学信息泛滥，误导大众
- 缺乏个性化的解决方案

## {sections[2]}
### 底层逻辑
{extract_core_title(title)}的核心本质是{extract_core_title(title)}的供需平衡，既要满足基本需求，又要避免过度消耗。

### 影响因素
1. 外部环境：社会文化、经济条件、科技发展
2. 个人因素：年龄、性别、生活习惯、认知水平
3. 互动关系：家庭、社交、职场的相互影响

## {sections[3]}
### 短期建议
1. 信息筛选：辨别权威来源，避免轻信非专业信息
2. 小步尝试：从简单易行的方法开始，逐步调整
3. 记录反馈：跟踪实施效果，及时优化方案

### 长期规划
1. 建立体系：形成适合自己的完整解决方案
2. 持续学习：关注最新研究和实践成果
3. 分享交流：和他人分享经验，互相启发

## {sections[4]}
- 避免急于求成，任何改变都需要时间
- 尊重个体差异，没有放之四海而皆准的方法
- 关注长期效果，而非短期速成
- 遇到问题及时调整，不要固执己见

## {sections[5]}
{extract_core_title(title)}是一个持续探索的过程。通过科学的方法和开放的心态，每个人都能找到适合自己的解决方案，让生活更加美好。
"""
    
    article = article_content
    with open(f"{DATA_DIR}/article.json", "w", encoding="utf-8") as f:
        json.dump({
            "title": title,
            "article": article,
            "word_count": len(article.replace("\n", "").replace("#", "").replace("##", ""))
        }, f, ensure_ascii=False)
    
    log(f"[4] 正文: {len(article)}字 (纯文本: {len(article.replace('\n', '').replace('#', '').replace('##', ''))}字)")
    return article

def node5_summary():
    try:
        with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
            data = json.load(f)
        # 智能摘要：提取核心内容，而非简单截断
        article = data["article"]
        # 提取所有二级标题后的第一段内容
        paragraphs = article.split("## ")[1:]
        summary_parts = []
        for p in paragraphs[:3]:  # 取前3个章节
            content = p.split("\n")[1:][0].strip()  # 取章节下第一段
            if content:
                summary_parts.append(content)
        summary = "；".join(summary_parts[:2]) + "..."  # 最多2个核心点
        if len(summary) < 20:  # 兜底
            summary = article[:180].strip() + "..."
    except:
        summary = "本文结合科学研究和实践经验，为中老年人提供了全面的健康养生/家庭情感解决方案，内容实用、科学、易懂。"
    
    with open(f"{DATA_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary}, f, ensure_ascii=False)
    
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
        token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        r = requests.get(token_url, timeout=10)
        token_resp = r.json()
        token = token_resp.get("access_token")
        
        if not token:
            errcode = token_resp.get("errcode", "unknown")
            errmsg = token_resp.get("errmsg", "unknown")
            log(f"[6] token失败: {errcode} - {errmsg}")
            return {"status": "failed", "error": f"token: {errcode} - {errmsg}"}
        log(f"[6] token成功!")
        
        log("[6] 上传永久封面...")
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb"
        files = {"media": ("cover.png", png_data, "image/png")}
        r = requests.post(upload_url, files=files, timeout=30)
        upload_result = r.json()
        thumb_media_id = upload_result.get("media_id")
        
        if not thumb_media_id:
            log(f"[6] 上传封面失败: {upload_result}")
            return {"status": "failed", "error": f"上传封面失败"}
        
        log(f"[6] 封面ID: {thumb_media_id}")

        # ==============================
        # 🔴 关键修复：强制标题 ≤ 60 字节
        # ==============================
        try:
            with open(f"{DATA_DIR}/article.json", encoding="utf-8") as f:
                data = json.load(f)
            title = data["title"]

            # 强制截断到 60 字节（绝对不会超公众号 64 限制）
            title_bytes = title.encode("utf-8")
            if len(title_bytes) > 60:
                title = title_bytes[:60].decode("utf-8", errors="ignore")
                log(f"[6] 标题超长，已自动截断: {title}")

            article = data["article"]
            with open(f"{DATA_DIR}/summary.json", encoding="utf-8") as f:
                summary = json.load(f)["summary"]
        except:
            title = "中老年人科学养生指南"
            article = "健康养生知识分享"
            summary = "科学实用的养生建议"

        log(f"[6] 最终发送标题: {title}  字节数={len(title.encode())}")
        
        html = f"<div style='font-size:16px;line-height:1.8;'>{article.replace(chr(10), '<br/>')}</div>"
        draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        
        article_data = {
            "title": title,
            "author": "AI助手",
            "digest": summary[:100],
            "content": html,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }
        
        r = requests.post(draft_url, json={"articles": [article_data]}, timeout=30)
        result = r.json()
        log(f"[6] 草稿结果: {result}")
        
        if "media_id" in result:
            log(f"[6] ✅ 草稿发布成功！")
            return {"status": "success", "media_id": result["media_id"]}
        else:
            log(f"[6] ❌ 草稿发布失败: {result}")
            return {"status": "failed", "error": str(result)}
            
    except Exception as e:
        log(f"[6] 异常: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

@app.route("/")
def index():
    return "内容生产流水线已启动！<br/>访问 /trigger 触发生产流程"

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": str(datetime.now())})

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
        
        return jsonify({
            "success": True, 
            "result": result,
            "timestamp": str(datetime.now())
        })
    except Exception as e:
        log(f"流水线错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": str(datetime.now())
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # 生产环境禁用debug
    app.run(host="0.0.0.0", port=port, debug=False)