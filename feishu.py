# -*- coding: utf-8 -*-
"""
飞书集成模块
- 获取 access_token
- 创建/管理多维表格
- 写入文章记录
- 创建飞书文档
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
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "") or os.environ.get("QCLAW_FEISHU_APP_SECRET", "")
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
        ("飞书文档", 15, None),
        ("微信状态", 3, {"options": [{"name": "草稿"}, {"name": "已发布"}, {"name": "未发"}]}),
        ("封面图", 15, None),
        ("素材来源", 1, None),
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
        "飞书文档": {"link": record_data.get("doc_url", ""), "text": "打开文档"},
        "微信状态": "草稿",
        "封面图": {"link": record_data.get("cover_url", ""), "text": "封面"},
        "素材来源": record_data.get("source", "网络"),
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


def push_to_feishu(title, article, summary, weekday, theme_info):
    """推送到飞书文档 + 多维表格"""
    try:
        # 获取 access_token
        access_token = get_feishu_token()
        if not access_token:
            return None
        
        # 构造文档内容（飞书 JSON 格式）
        date_str = beijing_now().strftime("%Y-%m-%d")
        theme_name = theme_info.get("name", "健康养生")
        theme_day = WEEKDAY_NAMES[weekday]
        
        # 文档标题：2026-04-12 周一情感心理 - 老人孤独感如何化解
        doc_title = f"{date_str} {theme_day}{theme_name} - {title}"
        
        # 飞书文档块格式
        blocks = [
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📅 {date_str} {theme_day} · {theme_name}"}], "text_styles": {"bold": True}}},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📌 主题：{theme_info.get('theme', '')}"}]}},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📝 来源：{article.get('source', '网络')}"}]}},
            {"block_type": 1, "is_collapsible": False, "layout": "paragraph", "elements": []},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"🏷️ 标题：{title}"}], "text_styles": {"bold": True}}},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": f"📋 摘要：{summary}"}]}},
            {"block_type": 1, "is_collapsible": False, "layout": "paragraph", "elements": []},
            {"block_type": 2, "text": {"elements": [{"type": "text_run", "text": "📄 正文："}], "text_styles": {"bold": True}}},
        ]
        
        # 正文分段（飞书每块有限制）
        article_lines = article.get("article", "").split("\n")
        for line in article_lines[:100]:  # 限制100行
            if line.strip():
                blocks.append({"block_type": 2, "text": {"elements": [{"type": "text_run", "text": line}]}})
        
        # 创建文档
        create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        headers = {"Authorization": f"Bearer {access_token}"}
        create_resp = requests.post(create_url, headers=headers, json={"document_id": "", "title": doc_title}, timeout=10)
        create_data = create_resp.json()
        
        if create_data.get("code") != 0:
            log(f"[飞书] 创建文档失败: {create_data}")
            return None
        
        doc_token = create_data["data"]["document"]["token"]
        
        # 写入内容块
        children_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
        children_resp = requests.post(children_url, headers=headers, json={"children": blocks, "index": -1}, timeout=30)
        children_data = children_resp.json()
        
        if children_data.get("code") != 0:
            log(f"[飞书] 写入内容失败: {children_data}")
            # 继续尝试写表
        else:
            log(f"[飞书] 文档内容写入成功")
        
        # 生成分享链接
        share_url = f"https://feishu.cn/docx/{doc_token}"
        log(f"[飞书] 文档已创建: {share_url}")
        
        # 写入多维表格
        log(f"[飞书] 开始写入多维表格...")
        table_id = ensure_articles_table(access_token)
        log(f"[飞书] 获取到表ID: {table_id}")
        if table_id:
            record_data = {
                "date": int(time.time()),
                "weekday": theme_day,
                "theme": theme_info.get("name", ""),
                "title": title,
                "summary": summary,
                "doc_url": share_url,
                "cover_url": article.get("cover_url", ""),
                "source": article.get("source", "网络"),
            }
            log(f"[飞书] 准备写入记录: {record_data}")
            record_id = write_article_record(access_token, table_id, record_data)
            log(f"[飞书] 记录写入结果: {record_id}")
        else:
            log(f"[飞书] 未获取到表ID，跳过写表")
        
        return share_url
        
    except Exception as e:
        import traceback
        log(f"[飞书] 推送异常: {e}")
        log(f"[飞书] 异常详情: {traceback.format_exc()}")
        return None
