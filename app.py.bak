# -*- coding: utf-8 -*-
import os, re, time, json, requests
from datetime import datetime, timezone, timedelta

# 新增：读取历史文章防重复
def read_last_articles(weekday, limit=4):
    """读取最近几周同主题的正文，返回拼接的上下文字符串，供生成时注入防重复"""
    try:
        app_id = os.environ.get("FEISHU_APP_ID", "")
        app_secret = os.environ.get("FEISHU_APP_SECRET", "")
        if not app_id or not app_secret:
            return ""

        # 获取 token
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret}, timeout=10
        )
        token_data = resp.json()
        token = token_data.get("tenant_access_token", "")
        if not token:
            return ""

        headers = {"Authorization": f"Bearer {token}"}
        table_id = os.environ.get("FEISHU_ARTICLES_TABLE_ID", "tbl3jVfVkQZwlyIv")
        bitable_token = os.environ.get("FEISHU_BITABLE_TOKEN", "THaEbbUfWak0d2sVpCbcXW4Dnfe")
        weekday_name = ["周一","周二","周三","周四","周五","周六","周日"][weekday]
        weekday_filter = f'AND(Filter("星期", "=", "{weekday_name}"), NOT(Filter("标题", "is_empty"))'

        # 分页读取所有记录
        all_records = []
        page_token = None
        for _ in range(10):  # 最多 10 页
            params = {
                "page_size": 100,
                "filter": weekday_filter,
                "sort_by": "ctime",
                "order_by": "Desc",
            }
            if page_token:
                params["page_token"] = page_token
            r = requests.get(
                f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables/{table_id}/records",
                headers=headers, params=params, timeout=15
            )
            d = r.json()
            if d.get("code") != 0:
                break
            items = d.get("data", {}).get("items", [])
            if not items:
                break
            all_records.extend(items)
            page_token = d.get("data", {}).get("page_token")
            if not page_token:
                break
            time.sleep(0.3)

        if not all_records:
            return ""

        # 取最近 limit 条（按创建时间倒序）
        records = all_records[:limit]
        parts = []
        for rec in records:
            fields = rec.get("fields", {})
            title = fields.get("标题", "")
            body = fields.get("正文", "")
            ctime = rec.get("created_time", "")[:10]
            if body:
                parts.append(f"【{ctime} {title}】\n{body[:1200]}")
            elif title:
                parts.append(f"【{ctime} {title}】")

        if not parts:
            return ""

        context = (
            f"\n\n【注意】近{len(parts)}周写过类似主题，摘要如下，"
            f"本文要用完全不同的角度、案例和数据：\n\n"
            + "\n\n---\n\n".join(parts)
            + "\n\n【重要】以上仅供参考，本文必须从全新角度展开，禁止重复使用上述案例或数据。"
        )
        return context

    except Exception as e:
        return ""

