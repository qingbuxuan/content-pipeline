# -*- coding: utf-8 -*-
"""
飞书集成模块
- 获取 access_token
- 创建/管理多维表格
- 写入文章记录（正文+封面提示词直接存表格）
"""

import os
import requests
import time

from config import (
    FEISHU_BITABLE_TOKEN,
    WEEKDAY_NAMES,
)
from utils import log, beijing_now

# 模块级缓存
FEISHU_ARTICLES_TABLE_ID = None


def get_feishu_token():
    """获取飞书 access_token"""
    # 兼容多种环境变量命名格式
    app_id = (
        os.environ.get("FEISHU_APP_ID", "") or
        os.environ.get("QCLAW_FEISHU_APP_ID", "") or
        os.environ.get("QCLAW_FEISHU_ACCOUNT_CLI_A94FFD179EB9DCB0_APPID", "")
    )
    app_secret = (
        os.environ.get("FEISHU_APP_SECRET", "") or
        os.environ.get("QCLAW_FEISHU_APP_SECRET", "") or
        os.environ.get("QCLAW_FEISHU_ACCOUNT_CLI_A94FFD179EB9DCB0_APPSECRET", "")
    )
    if not app_id or not app_secret:
        log(f"[飞书] 环境变量缺失: app_id={'有' if app_id else '无'}, app_secret={'有' if app_secret else '无'}")
        return None
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        log(f"[飞书] Token获取失败 code={data.get('code')}: {data.get('msg', data)}")
        return None
    if "tenant_access_token" not in data:
        log(f"[飞书] Token响应格式异常: {str(data)[:200]}")
        return None
    return data["tenant_access_token"]


def ensure_articles_table(token):
    """确保公众号文章记录表存在，创建必要的字段，返回 table_id"""
    global FEISHU_ARTICLES_TABLE_ID
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 列出现有表
    list_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables"
    list_resp = requests.get(list_url, headers=headers, timeout=10)
    list_data = list_resp.json()
    
    if list_data.get("code") != 0:
        log(f"[飞书] 获取表格列表失败: {list_data}")
        return None
    
    table_id = None
    for table in list_data.get("data", {}).get("items", []):
        if table.get("name") == "公众号文章记录":
            table_id = table.get("table_id")
            FEISHU_ARTICLES_TABLE_ID = table_id
            log(f"[飞书] 找到公众号文章记录表: {table_id}")
            break
    
    # 2. 不存在则创建
    if not table_id:
        log("[飞书] 创建公众号文章记录表...")
        create_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables"
        create_resp = requests.post(create_url, headers=headers, json={"table": {"name": "公众号文章记录"}}, timeout=10)
        create_data = create_resp.json()
        
        if create_data.get("code") != 0:
            log(f"[飞书] 创建表失败: {create_data}")
            return None
        
        table_id = create_data["data"]["table_id"]
        FEISHU_ARTICLES_TABLE_ID = table_id
        log(f"[飞书] 表创建成功: {table_id}")
    
    # 3. 查询现有字段
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/fields"
    fields_resp = requests.get(fields_url, headers=headers, timeout=10)
    fields_data = fields_resp.json()
    existing_field_names = {f["field_name"] for f in fields_data.get("data", {}).get("items", [])}
    log(f"[飞书] 现有字段: {existing_field_names}")
    
    # 4. 定义需要创建的字段
    field_defs = [
        ("日期", 5, None),
        ("星期", 3, {"options": [{"name": n} for n in WEEKDAY_NAMES]}),
        ("主题", 3, {"options": [{"name": "情感心理"}, {"name": "养生生活"}, {"name": "慢病管理"}, {"name": "情绪养生"}, {"name": "生活品质"}, {"name": "科技健康"}, {"name": "科普急救"}]}),
        ("标题", 1, None),
        ("摘要", 1, None),
        ("正文", 1, None),
        ("封面提示词", 1, None),
        ("素材来源", 1, None),
        ("微信状态", 3, {"options": [{"name": "草稿"}, {"name": "已发布"}, {"name": "未发"}]}),
        ("封面图", 15, None),
    ]
    
    # 5. 创建缺失的字段
    for field_name, field_type, field_property in field_defs:
        if field_name in existing_field_names:
            log(f"[飞书] 字段已存在，跳过: {field_name}")
            continue
        
        field_payload = {"field_name": field_name, "type": field_type}
        if field_property:
            field_payload["property"] = field_property
        
        create_field_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/fields"
        create_resp = requests.post(create_field_url, headers=headers, json=field_payload, timeout=10)
        result = create_resp.json()
        
        if result.get("code") != 0:
            log(f"[飞书] 创建字段失败 [{field_name}]: {result}")
        else:
            log(f"[飞书] 字段创建成功: {field_name} (type={field_type})")
    
    # 6. 再次验证
    verify_resp = requests.get(fields_url, headers=headers, timeout=10)
    verify_data = verify_resp.json()
    final_fields = [f["field_name"] for f in verify_data.get("data", {}).get("items", [])]
    log(f"[飞书] 最终字段列表: {final_fields}")
    
    return table_id


def write_article_record(token, table_id, record_data):
    """写入公众号文章记录到多维表格（自动适配实际字段名）"""
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 查询实际字段名
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/fields"
    fields_resp = requests.get(fields_url, headers=headers, timeout=10)
    fields_data = fields_resp.json()

    if fields_data.get("code") != 0:
        log(f"[飞书] 查询字段失败: {fields_data}")
        return None

    actual_fields = {f["field_name"]: f for f in fields_data.get("data", {}).get("items", [])}
    log(f"[飞书] 实际字段: {list(actual_fields.keys())}")

    # 2. 字段名映射（中文名 -> 值）
    field_mapping = {
        "日期": record_data.get("date", 0) * 1000,
        "星期": record_data.get("weekday", ""),
        "主题": record_data.get("theme", ""),
        "标题": record_data.get("title", ""),
        "摘要": record_data.get("summary", ""),
        "正文": record_data.get("article", ""),
        "封面提示词": record_data.get("cover_prompt", ""),
        "素材来源": record_data.get("source", "网络"),
        "微信状态": "草稿",
        "封面图": {"link": record_data.get("cover_url", ""), "text": "封面"},
    }

    # 3. 用实际字段名构造写入数据
    fields_to_write = {}
    for cn_name, value in field_mapping.items():
        matched_name = None
        if cn_name in actual_fields:
            matched_name = cn_name
        else:
            # 模糊匹配
            for fname in actual_fields:
                if cn_name in fname or fname in cn_name:
                    matched_name = fname
                    break
        if matched_name:
            fields_to_write[matched_name] = value
        else:
            log(f"[飞书] 跳过字段（未找到）: {cn_name}")

    # 4. 写入记录
    write_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{table_id}/records"
    resp = requests.post(write_url, headers=headers, json={"fields": fields_to_write}, timeout=10)
    data = resp.json()

    if data.get("code") != 0:
        log(f"[飞书] 写入记录失败: {data}")
        return None

    log("[飞书] 记录写入成功")
    return data.get("data", {}).get("record", {}).get("record_id")


def push_to_feishu(title, article_data, summary, weekday, theme_info, cover_prompt=""):
    """推送到飞书多维表格（正文+封面提示词直接存表格，不再创建飞书文档）"""
    try:
        # 获取 access_token
        access_token = get_feishu_token()
        if not access_token:
            return None
        
        date_str = beijing_now().strftime("%Y-%m-%d")
        theme_name = theme_info.get("name", "健康养生")
        theme_day = WEEKDAY_NAMES[weekday]

        # 写入多维表格
        log(f"[飞书] 开始写入多维表格...")
        table_id = ensure_articles_table(access_token)
        log(f"[飞书] 获取到表ID: {table_id}")
        if not table_id:
            log(f"[飞书] 未获取到表ID，跳过写表")
            return None

        record_data = {
            "date": int(time.time()),
            "weekday": theme_day,
            "theme": theme_info.get("name", ""),
            "title": title,
            "summary": summary,
            "article": article_data.get("article", ""),
            "cover_prompt": cover_prompt,
            "cover_url": article_data.get("cover_url", ""),
            "source": article_data.get("source", "网络"),
        }
        log(f"[飞书] 准备写入记录: 标题={title}, 正文={len(record_data['article'])}字, 封面提示词={len(cover_prompt)}字")
        record_id = write_article_record(access_token, table_id, record_data)
        log(f"[飞书] 记录写入结果: {record_id}")

        if record_id:
            bitable_url = f"https://feishu.cn/base/{FEISHU_BITABLE_TOKEN}/table/{table_id}/record/{record_id}"
            log(f"[飞书] 记录已创建: {bitable_url}")
            return bitable_url
        return None
        
    except Exception as e:
        import traceback
        log(f"[飞书] 推送异常: {e}")
        log(f"[飞书] 异常详情: {traceback.format_exc()}")
        return None
