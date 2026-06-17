# -*- coding: utf-8 -*-
"""扩展数据采集模块：节气养生、食材卡路里、健康计算、健康小贴士"""
from config import *
import requests, json, random

# ========== API Token ==========
ISTEREO_TOKEN = os.environ.get("ISTEREO_TOKEN", "")
ISTEREO_BASE = "https://api.istero.com"
ISTEREO_HEADERS = {"Authorization": f"Bearer {ISTEREO_TOKEN}"} if ISTEREO_TOKEN else {}

# ========== 二十四节气 ==========
# 内置24节气养生数据（API fallback）
SOLAR_TERMS_DATA = {
    "小寒": {
        "months": [1], "health": "防寒保暖、温补肾阳、早睡晚起、适当进补",
        "diet": "羊肉、核桃、桂圆、红枣、生姜、糯米",
        "avoid": "生冷食物、过度劳累、过早外出晨练"
    },
    "大寒": {
        "months": [1], "health": "御寒保暖、固护肾气、预防心脑血管疾病",
        "diet": "糯米、红枣、莲子、花生、鸡肉、牛肉",
        "avoid": "寒凉食物、剧烈运动、饮酒过量"
    },
    "立春": {
        "months": [2], "health": "养肝护肝、早起舒展、防风御寒、保持心情舒畅",
        "diet": "韭菜、香葱、菠菜、荠菜、春笋、豆芽",
        "avoid": "酸味过重、油腻食物、过度劳累"
    },
    "雨水": {
        "months": [2], "health": "祛湿健脾、预防倒春寒、保持情绪平稳",
        "diet": "山药、薏米、红豆、蜂蜜、红枣、小米",
        "avoid": "生冷寒凉、甜食过多、湿气重的食物"
    },
    "惊蛰": {
        "months": [3], "health": "疏肝理气、预防感冒、适当运动升发阳气",
        "diet": "梨、银耳、菠菜、春笋、芹菜、枸杞",
        "avoid": "辛辣刺激、过度疲劳、情志不畅"
    },
    "春分": {
        "months": [3], "health": "阴阳平衡、调养脾胃、预防过敏、保持平和心态",
        "diet": "荠菜、春笋、菠菜、鸡蛋、豆芽、山药",
        "avoid": "偏寒偏热食物、过度进补"
    },
    "清明": {
        "months": [4], "health": "养肝清肺、适度踏青、预防花粉过敏、调节情绪",
        "diet": "菠菜、荠菜、芹菜、鸡蛋、银耳、蜂蜜",
        "avoid": "辛辣油腻、过度忧伤、花粉过敏者注意防护"
    },
    "谷雨": {
        "months": [4], "health": "健脾祛湿、预防感冒、注意早晚温差",
        "diet": "薏米、山药、红豆、冬瓜、鲫鱼、绿豆",
        "avoid": "生冷寒凉、油腻食物、过度出汗"
    },
    "立夏": {
        "months": [5], "health": "养心安神、清淡饮食、适当午休、防止中暑",
        "diet": "苦瓜、莲子、绿豆、冬瓜、丝瓜、西瓜",
        "avoid": "油腻厚味、过度运动、大汗淋漓"
    },
    "小满": {
        "months": [5], "health": "清热祛湿、预防皮肤病、注意饮食卫生",
        "diet": "冬瓜、苦瓜、薏米、丝瓜、绿豆、芹菜",
        "avoid": "辛辣油腻、生冷不洁食物、潮湿环境久留"
    },
    "芒种": {
        "months": [6], "health": "清热解暑、注意湿气、预防肠道疾病、午休补阳",
        "diet": "绿豆、苦瓜、西瓜、冬瓜、薏米、酸梅汤",
        "avoid": "肥甘厚腻、暴饮暴食、空调温度过低"
    },
    "夏至": {
        "months": [6], "health": "养心安神、清热消暑、保护阳气、适当午睡",
        "diet": "西瓜、绿豆、苦瓜、黄瓜、西红柿、酸梅汤",
        "avoid": "生冷过度、冷饮冰水、长时间空调房"
    },
    "小暑": {
        "months": [7], "health": "防暑降温、祛湿健脾、保护心气、三伏养生开始",
        "diet": "绿豆汤、西瓜、荷叶粥、冬瓜、薏米、莲子",
        "avoid": "暴饮暴食、过度贪凉、烈日暴晒"
    },
    "大暑": {
        "months": [7], "health": "清热解暑、防湿气、护脾胃、冬病夏治最佳时机",
        "diet": "西瓜、绿豆、荷叶、薏米、苦瓜、冬瓜汤",
        "avoid": "冷饮过多、油腻厚味、烈日下长时间活动"
    },
    "立秋": {
        "months": [8], "health": "润肺养阴、适度贴秋膘、早睡早起、预防秋燥",
        "diet": "梨、银耳、百合、蜂蜜、莲藕、山药",
        "avoid": "辛辣刺激、过度进补、熬夜"
    },
    "处暑": {
        "months": [8], "health": "润肺生津、调整作息、预防秋燥、适度运动",
        "diet": "梨、银耳、百合、蜂蜜、鸭肉、莲藕",
        "avoid": "辛辣烧烤、过度贪凉、干燥环境"
    },
    "白露": {
        "months": [9], "health": "润肺防燥、注意保暖、预防呼吸道疾病",
        "diet": "银耳、百合、梨、核桃、花生、龙眼",
        "avoid": "辛辣刺激、生冷寒凉、过早脱减衣物"
    },
    "秋分": {
        "months": [9], "health": "阴阳平衡、润肺养胃、调节情志、预防秋乏",
        "diet": "山药、百合、银耳、梨、石榴、栗子",
        "avoid": "辛辣油腻、过度进补、情绪波动"
    },
    "寒露": {
        "months": [10], "health": "养阴润燥、保暖防寒、预防心脑血管疾病",
        "diet": "芝麻、核桃、银耳、百合、蜂蜜、柿子",
        "avoid": "生冷寒凉、辛辣刺激、过早脱衣"
    },
    "霜降": {
        "months": [10], "health": "健脾养胃、润肺防燥、防寒保暖、适当进补",
        "diet": "栗子、花生、柿子、梨、山药、南瓜",
        "avoid": "辛辣刺激、生冷食物、过度劳累"
    },
    "立冬": {
        "months": [11], "health": "养藏补肾、温补阳气、早睡晚起、预防感冒",
        "diet": "羊肉、牛肉、核桃、桂圆、红枣、黑芝麻",
        "avoid": "生冷寒凉、过度运动、出汗过多"
    },
    "小雪": {
        "months": [11], "health": "温补肾阳、御寒保暖、预防心脑血管、注意情绪调节",
        "diet": "羊肉、鸡肉、核桃、栗子、山药、红枣",
        "avoid": "寒凉食物、情绪低落、户外运动过久"
    },
    "大雪": {
        "months": [12], "health": "防寒保暖、进补养肾、预防关节疼痛、注意室内通风",
        "diet": "羊肉、狗肉、核桃、桂圆、当归、枸杞",
        "avoid": "生冷寒凉、过度进补、长时间不活动"
    },
    "冬至": {
        "months": [12], "health": "进补养阳、温肾健脾、预防心脑血管、适当泡脚",
        "diet": "饺子、羊肉汤、核桃、红枣、汤圆、黑芝麻",
        "avoid": "生冷食物、过度劳累、情绪激动"
    }
}

def get_solar_term(date_str=None):
    """获取当日节气信息（API优先，内置数据fallback）
    
    Args:
        date_str: 日期字符串 YYYY-MM-DD，默认今天
        
    Returns:
        dict: {name, proverb, custom, description, climate, health, diet, avoid} 或 None
    """
    now = beijing_now()
    date = date_str or now.strftime("%Y-%m-%d")
    
    # 先尝试 API
    if ISTEREO_TOKEN:
        try:
            r = requests.get(f"{ISTEREO_BASE}/resource/v1/solar/terms/query",
                           params={"date": date, "token": ISTEREO_TOKEN}, timeout=10)
            if r.status_code == 200:
                j = r.json()
                if j.get("code") == 200 and j.get("data"):
                    data = j["data"]
                    term_name = data.get("name", "")
                    # 补充内置养生数据
                    builtin = SOLAR_TERMS_DATA.get(term_name, {})
                    return {
                        "name": term_name,
                        "proverb": data.get("proverb", ""),
                        "custom": data.get("custom", ""),
                        "description": data.get("description", ""),
                        "climate": data.get("climate", ""),
                        "health": builtin.get("health", ""),
                        "diet": builtin.get("diet", ""),
                        "avoid": builtin.get("avoid", "")
                    }
        except Exception as e:
            log(f"[节气] API调用失败: {e}")
    
    # Fallback: 根据月份查找当月节气
    month = now.month if not date_str else int(date_str.split("-")[1])
    for term_name, info in SOLAR_TERMS_DATA.items():
        if month in info.get("months", []):
            return {
                "name": term_name,
                "proverb": f"今日{term_name}，注意养生。",
                "custom": "",
                "description": f"{term_name}时节，顺应自然，调养身心。",
                "climate": "",
                "health": info["health"],
                "diet": info["diet"],
                "avoid": info["avoid"]
            }
    
    return None

def get_nearby_solar_term():
    """获取最近的节气（前后15天内），用于非节气日的养生提示"""
    now = beijing_now()
    month = now.month
    day = now.day
    
    # 按月找到当月的节气
    for term_name, info in SOLAR_TERMS_DATA.items():
        if month in info.get("months", []):
            # 找到两个节气中更近的一个（上旬=前一个，下旬=后一个）
            pass
    
    # 简化：直接返回当月的养生建议
    for term_name, info in SOLAR_TERMS_DATA.items():
        if month in info.get("months", []):
            return {
                "name": term_name,
                "health": info["health"],
                "diet": info["diet"],
                "avoid": info["avoid"]
            }
    return None


# ========== 食物卡路里 ==========
def get_food_calories(food_name):
    """查询食物卡路里
    
    Args:
        food_name: 食物名称（如"米饭"、"鸡蛋"）
        
    Returns:
        list: [{"name": "米饭", "calorie": "116大卡/100克"}, ...] 或 None
    """
    if not ISTEREO_TOKEN:
        return None
    try:
        r = requests.get(f"{ISTEREO_BASE}/resource/v1/food/calorie/query",
                        params={"food": food_name, "token": ISTEREO_TOKEN}, timeout=10)
        if r.status_code == 200:
            j = r.json()
            if j.get("code") == 200 and j.get("data"):
                return j["data"].get("lists", [])[:5]  # 返回前5个结果
    except Exception as e:
        log(f"[食材] 卡路里查询失败({food_name}): {e}")
    return None

def get_random_food_tip():
    """随机获取一个常见食材的卡路里信息作为养生小知识"""
    foods = ["米饭", "鸡蛋", "豆腐", "西红柿", "黄瓜", "芹菜", "鸡肉", "鱼肉", 
             "苹果", "香蕉", "红薯", "山药", "绿豆", "红豆", "薏米", "枸杞"]
    food = random.choice(foods)
    data = get_food_calories(food)
    if data:
        top = data[0]
        return f"【{top['name']}】{top.get('calorie', '')}"
    return None


# ========== 健康计算工具 ==========
def calculate_bmi(height_cm, weight_kg):
    """BMI计算（API优先，内置公式fallback）
    
    Returns: {"bmi": 22.49, "interpretation": "正常范围"} 或 None
    """
    if ISTEREO_TOKEN:
        try:
            r = requests.get(f"{ISTEREO_BASE}/resource/v1/bmi/query",
                           params={"height": height_cm, "weight": weight_kg, "token": ISTEREO_TOKEN},
                           timeout=10)
            if r.status_code == 200:
                j = r.json()
                if j.get("code") == 200 and j.get("data"):
                    return j["data"]
        except:
            pass
    
    # Fallback: 内置公式
    try:
        bmi = weight_kg / ((height_cm / 100) ** 2)
        bmi = round(bmi, 2)
        if bmi < 18.5:
            interp = "偏瘦"
        elif bmi < 24:
            interp = "正常范围"
        elif bmi < 28:
            interp = "偏胖"
        else:
            interp = "肥胖"
        return {"bmi": bmi, "interpretation": interp}
    except:
        return None

def calculate_bmr(age, gender, height_cm, weight_kg):
    """基础代谢率计算
    gender: 1=男, 2=女
    
    Returns: {"bmr": 1633.07, "interpretation": "..."} 或 None
    """
    if ISTEREO_TOKEN:
        try:
            r = requests.get(f"{ISTEREO_BASE}/resource/v1/bmr/query",
                           params={"age": age, "gender": gender, "height": height_cm, 
                                  "weight": weight_kg, "token": ISTEREO_TOKEN},
                           timeout=10)
            if r.status_code == 200:
                j = r.json()
                if j.get("code") == 200 and j.get("data"):
                    return j["data"]
        except:
            pass
    
    # Fallback: Harris-Benedict公式
    try:
        if gender == 1:
            bmr = 88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age
        else:
            bmr = 447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age
        return {"bmr": round(bmr, 2), "interpretation": f"基础代谢约{round(bmr, 0)}卡路里/天"}
    except:
        return None


# ========== 健康小贴士（LLM生成） ==========
# 内置健康小贴士库（API不可用的fallback）
HEALTH_TIPS = [
    "每天喝够8杯水，早起一杯温水唤醒肠胃，睡前一杯温水保护血管。",
    "饭后不要马上散步，等30分钟再走，避免胃下垂。",
    "睡前2小时不要进食，给消化系统留足休息时间。",
    "每天坚持午休20-30分钟，可有效降低心血管疾病风险。",
    "走路是最好的运动，每天6000-8000步，强身健体不伤关节。",
    "久坐每45分钟起身活动5分钟，预防腰椎和下肢静脉血栓。",
    "早餐一定要吃好，一碗粥+一个鸡蛋+一份蔬菜，营养均衡。",
    "多吃深色蔬菜，菠菜、西兰花、紫甘蓝，抗氧化效果好。",
    "空调温度不要低于26度，定时通风换气，预防空调病。",
    "晒太阳15-20分钟，帮助合成维生素D，促进钙吸收。",
    "保持社交活动，和朋友聊天、下棋、跳广场舞，预防孤独和认知衰退。",
    "睡前泡脚15分钟，水温40度左右，促进血液循环，改善睡眠。",
    "每天吃一小把坚果（约25克），核桃、杏仁、花生，补充好脂肪。",
    "控制盐的摄入，每天不超过6克，预防高血压和心脑血管疾病。",
    "定期体检，血压、血糖、血脂、肝肾功能，早发现早治疗。",
    "心情好身体才好，遇事不要生气，笑一笑十年少。",
    "适当吃粗粮，小米、糙米、燕麦，膳食纤维助消化。",
    "减少久坐久躺，即使在家也可以做做伸展操、拍打经络。",
    "每天吃一个水果，苹果、橙子、猕猴桃，补充维生素。",
    "保持规律作息，尽量每天同一时间入睡和起床。",
    "食盐过多伤肾，做菜少放盐，多用醋、柠檬汁调味。",
    "看电视时间每次不超过1小时，起身活动保护眼睛和颈椎。",
    "泡茶喝养生，菊花明目、枸杞补肾、山楂消食，各有所长。",
    "散步时挺胸抬头，呼吸新鲜空气，是最简单的养生法。",
    "睡前少看手机，蓝光影响褪黑素分泌，容易失眠。",
    "喝酸奶助消化，选择低糖或无糖的，补充益生菌。",
    "太极拳、八段锦适合中老年人，动作柔和，强身健体。",
    "保持良好的排便习惯，定时排便，预防肠道疾病。",
    "秋季干燥多喝水，冬季寒冷多喝汤，夏季炎热多喝绿茶。",
    "控制晚餐分量，七分饱最好，不给肠胃增加负担。",
]

def get_health_tip():
    """获取每日健康小贴士（随机内置 + 可选LLM生成）
    
    Returns: str 健康小贴士文本
    """
    tip = random.choice(HEALTH_TIPS)
    log(f"[健康贴士] 随机选取: {tip[:30]}...")
    return tip


# ========== 腾讯健康频道（待实现） ==========
def get_tencent_health_news():
    """获取腾讯健康频道最新资讯（待研究可用接口）
    
    Returns: list[dict] 或 None
    """
    # TODO: 研究腾讯健康频道的可用接口
    # 可能的来源：腾讯RSS、爬取网页、或第三方聚合
    return None


# ========== 综合素材采集 ==========
def collect_enhanced_materials():
    """采集扩展素材，整合所有新数据源，返回可注入prompt的文本
    
    Returns:
        str: 格式化的素材文本，可直接拼入prompt
    """
    parts = []
    
    # 1. 节气养生
    solar = get_solar_term()
    if solar:
        parts.append(f"【节气养生·{solar['name']}】")
        parts.append(f"谚语：{solar.get('proverb', '')}")
        if solar.get('custom'):
            parts.append(f"习俗：{solar['custom']}")
        if solar.get('climate'):
            parts.append(f"气候：{solar['climate']}")
        parts.append(f"养生要点：{solar.get('health', '')}")
        parts.append(f"推荐饮食：{solar.get('diet', '')}")
        if solar.get('avoid'):
            parts.append(f"注意事项：{solar['avoid']}")
        parts.append("")
    else:
        # 非节气日：显示最近节气提示
        nearby = get_nearby_solar_term()
        if nearby:
            parts.append(f"【当月节气·{nearby['name']}相关养生】")
            parts.append(f"养生要点：{nearby.get('health', '')}")
            parts.append(f"推荐饮食：{nearby.get('diet', '')}")
            parts.append("")
    
    # 2. 健康小贴士
    tip = get_health_tip()
    if tip:
        parts.append(f"【今日健康小贴士】{tip}")
        parts.append("")
    
    # 3. 随机食材知识
    food_tip = get_random_food_tip()
    if food_tip:
        parts.append(f"【食材小知识】{food_tip}")
        parts.append("")
    
    result = "\n".join(parts).strip()
    if result:
        log(f"[扩展素材] 采集完成，共{len(result)}字")
    else:
        log("[扩展素材] 无可用素材")
    
    return result
