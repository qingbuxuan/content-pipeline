# -*- coding: utf-8 -*-
"""防重复方案：注入read_articles历史上下文到node4"""
import re

with open(r'C:\content-pipeline\app_merged.psy', 'r', encoding='utf-8') as f:
    content = f.read()

read_articles_code = '''
def read_articles(weekday, limit=4):
    """读取最近N篇同主题文章的摘要，避免重复角度"""
    try:
        app_ = os.environ.get("FEISHU_APP_ID", "")
        sec_ = os.environ.get("FEISHU_APP_SECRET", "")
        if not app_ or not sec_:
            return ""
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_, "app_secret": sec_}, timeout=10
        )
        token = resp.json().get("tenant_access_token", "")
        if not token:
            return ""
        hdr = {"Authorization": f"Bearer {token}"}
        tbl = os.environ.get("FEISHU_ARTICLES_TABLE_ID", "tbl3jVfVkQZwlyIv")
        btk = os.environ.get("FEISHU_BITABLE_TOKEN", "THaEbbUfWak0d2sVpCbcXW4Dnfe")
        wdnames = ["周一","周二","周三","周四","周五","周六","周日"]
        wname = wdnames[weekday] if 0 <= weekday <= 6 else "周一"
        params = {
            "page_size": 500,
            "filter": f'AND(Filter("星期", "=", "{wname}"), NOT(Filter("正文", "is_empty")))',
            "sort_by": "ctime",
            "order_by": "Desc",
            "field_names": "星期,标题,正文"
        }
        r = requests.get(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{btk}/tables/{tbl}/records",
            headers=hdr, params=params, timeout=15
        )
        items = r.json().get("data", {}).get("items", [])
        parts = []
        for item in items[:limit]:
            flds = item.get("fields", {})
            title = flds.get("标题", "未知")
            body = flds.get("正文", "")
            snippet = body[:300] if body else ""
            parts.append(f"标题：{title}\n{'' if len(snippet) < 50 else snippet + '...'}")
        if not parts:
            return ""
        return "\n\n---\n【近期同类文章参考，请选择不同切入角度】\n" + "\n---\n".join(parts)
    except:
        return ""
'''
target = '\ndef get_'
if target in content:
    content = content.replace(target, read_articles_code + target, 1)
    print("read_articles inserted OK")
else:
    print("ERROR: get_ not found")
    exit(1)

old = '    result = call_deepseek(THREE_'
new = '''    wk = weekday if "weekday" in dir() else 0
    hist = read_articles(wk, limit=4)
    pbase = THREE_HOOKS_ARTICLE_PROMPT
    if hist:
        pbase = pbase.replace(
            "## 标题\\n{title}",
            f"## 标题\\n{{title}}\\n{hist}"
        )
    result = call_deepseek(pbase.'''
if old in content:
    content = content.replace(old, new, 1)
    print("hist injection OK")
else:
    print("ERROR: call_deepseek not found at expected spot")
    exit(1)

with open(r'C:\content-pipeline\app_merged.psy', 'w', encoding='utf-8') as f:
    f.write(content)
print("SAVED OK")