from flask import Flask, jsonify, request
import os, json, requests, base64, hashlib, hmac, time, urllib.parse, io, re
from datetime import datetime, timezone, timedelta
from PIL import Image
import markdown

BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    return datetime.now(BEIJING_TZ)

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))
DATA_DIR = "/tmp/data"
os.makedirs(DATA_DIR, exist_ok=True)

SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
WANXIANG_API_KEY = os.environ.get("WANXIANG_API_KEY", "")
WX_APPID = os.environ.get("WX_APPID", "")
WX_APPSECRET = os.environ.get("WX_APPSECRET", "")

# ========== 七天主题样式系统 ==========
# 每天一个主题，每个主题一套配色方案
STYLE_THEMES = {
    0: {  # 周一 · 情感心理 - 温暖粉红调
        "name": "情感心理",
        "theme": "面对空巢与孤独，老人的情感需求正在被看见",
        "keywords": ["孤独", "空巢", "独居", "陪伴", "代际", "子女", "父母", "养老", "思念", "老年", "退休", "情感", "亲情", "家庭", "寂寞"],
        "direction": "如何面对独居/空巢/孤独感、代际沟通（如何与子女相处）",
        "colors": {
            "primary": "#e91e63",      # 主色：粉红
            "heading": "#880e4f",      # 标题色：深玫红
            "text": "#5d4037",         # 正文色：暖棕
            "strong": "#c2185b",       # 重点色：玫红
            "strong_bg": "#fce4ec",    # 重点背景：浅粉
            "quote_border": "#f48fb1", # 引用边框：浅粉红
            "quote_bg": "#fce4ec",     # 引用背景：浅粉
            "quote_text": "#880e4f",   # 引用文字：深玫红
            "tag": "#ad1457",          # 标签色：深粉
        }
    },
    1: {  # 周二 · 养生生活 - 清新绿色调
        "name": "养生生活",
        "theme": "中式轻养生，正在成为最易传播的日常内容",
        "keywords": ["养生", "中医", "食疗", "药食同源", "食谱", "饮食", "进补", "体质", "节气", "四季", "春季", "养肝", "健脾", "抗炎", "营养", "早餐", "晚餐"],
        "direction": "四季顺时养生（如春季防风护肝）、药食同源食谱、一日三餐怎么吃",
        "colors": {
            "primary": "#4caf50",
            "heading": "#2e7d32",
            "text": "#33691e",
            "strong": "#2e7d32",
            "strong_bg": "#e8f5e9",
            "quote_border": "#81c784",
            "quote_bg": "#f1f8e9",
            "quote_text": "#33691e",
            "tag": "#558b2f",
        }
    },
    2: {  # 周三 · 慢病管理 - 警示橙色调
        "name": "慢病管理",
        "theme": "三高、心血管等慢性病，正在成为最刚需的科普",
        "keywords": ["高血压", "高血糖", "高血脂", "三高", "糖尿病", "心梗", "中风", "脑梗", "心血管", "心脏病", "胆固醇", "血脂", "血糖", "血压", "慢性病", "服药", "用药"],
        "direction": "高血压/糖尿病怎么吃、用药常识（千万别犯的错）、慢病的日常监测与护理",
        "colors": {
            "primary": "#ff9800",
            "heading": "#e65100",
            "text": "#5d4037",
            "strong": "#e65100",
            "strong_bg": "#fff3e0",
            "quote_border": "#ffb74d",
            "quote_bg": "#fff8e1",
            "quote_text": "#e65100",
            "tag": "#ef6c00",
        }
    },
    3: {  # 周四 · 情绪养生 - 治愈紫色调
        "name": "情绪养生",
        "theme": "坏情绪比高血压更伤身，老年人的心理问题不容忽视",
        "keywords": ["抑郁", "焦虑", "失眠", "情绪", "心理健康", "孤独", "悲观", "心态", "老年痴呆", "阿尔茨海默", "记忆", "认知", "精神", "心理", "情绪管理"],
        "direction": "焦虑/抑郁的识别与应对、情绪急救方法、孤独感的排解、如何保持乐观心态",
        "colors": {
            "primary": "#9c27b0",
            "heading": "#6a1b9a",
            "text": "#4a148c",
            "strong": "#7b1fa2",
            "strong_bg": "#f3e5f5",
            "quote_border": "#ce93d8",
            "quote_bg": "#f3e5f5",
            "quote_text": "#6a1b9a",
            "tag": "#8e24aa",
        }
    },
    4: {  # 周五 · 生活品质 - 品质蓝色调
        "name": "生活品质",
        "theme": "银发族的消费升级，如何把钱花在刀刃上",
        "keywords": ["消费", "购物", "保健品", "营养品", "体检", "保险", "理财", "退休", "养老金", "省钱", "购物车", "礼物", "适老化", "产品", "测评", "避坑"],
        "direction": "健康消费避坑指南、适老化产品测评、如何科学选购保健品/家用医疗器械",
        "colors": {
            "primary": "#2196f3",
            "heading": "#1565c0",
            "text": "#0d47a1",
            "strong": "#1565c0",
            "strong_bg": "#e3f2fd",
            "quote_border": "#64b5f6",
            "quote_bg": "#e3f2fd",
            "quote_text": "#1565c0",
            "tag": "#1976d2",
        }
    },
    5: {  # 周六 · 科技健康 - 科技青色调
        "name": "科技健康",
        "theme": "AI与智能设备，正在改变老年人的健康管理方式",
        "keywords": ["手机", "APP", "智能", "科技", "AI", "人工智能", "健康码", "挂号", "预约", "视频", "微信", "网络", "智能手表", "血压计", "血糖仪", "健康监测"],
        "direction": "AI健康助手怎么用、智能监测设备推荐、科技如何帮老人老有所依",
        "colors": {
            "primary": "#00bcd4",
            "heading": "#00838f",
            "text": "#006064",
            "strong": "#00838f",
            "strong_bg": "#e0f7fa",
            "quote_border": "#4dd0e1",
            "quote_bg": "#e0f7fa",
            "quote_text": "#00838f",
            "tag": "#0097a7",
        }
    },
    6: {  # 周日 · 科普急救 - 紧急红色调
        "name": "科普急救",
        "theme": "关键时刻能救命的硬知识，是最能打动人心的内容",
        "keywords": ["急救", "心梗", "中风", "脑梗", "猝死", "心肺复苏", "急救常识", "家庭药箱", "常备药", "心脏病", "胸痛", "呼吸困难", "跌倒", "烫伤", "噎住", "异物"],
        "direction": "心脑血管疾病预防与急救、中风/心梗的识别与应对、家庭常备药品清单、用药安全指南",
        "colors": {
            "primary": "#f44336",
            "heading": "#c62828",
            "text": "#b71c1c",
            "strong": "#c62828",
            "strong_bg": "#ffebee",
            "quote_border": "#e57373",
            "quote_bg": "#ffebee",
            "quote_text": "#c62828",
            "tag": "#d32f2f",
        }
    }
}

# 兼容旧代码的 WEEKLY_THEMES
WEEKLY_THEMES = {k: {
    "name": v["name"],
    "theme": v["theme"],
    "keywords": v["keywords"],
    "direction": v["direction"]
} for k, v in STYLE_THEMES.items()}

KEYWORDS = ["健康", "养生", "中医", "运动", "睡眠", "心理", "情感", "饮食", "减肥", "健身", "血压", "血糖", "心脏", "癌症", "疫苗", "医院", "医生", "药品", "保健", "体检", "养老", "老年", "中年", "退休", "家庭", "婚姻", "孩子"]
