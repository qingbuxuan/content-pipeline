# -*- coding: utf-8 -*-
"""Markdown → HTML 样式转换，配合七天主题配色"""
from config import *
import markdown, re

def get_style_for_weekday(weekday):
    return STYLE_THEMES.get(weekday, STYLE_THEMES[0])["colors"]

def markdown_to_html(md_text, weekday):
    colors = get_style_for_weekday(weekday)
    
    # ========== 步骤0：清洗常见标签前缀 ==========
    md_text = re.sub(r'^金句收尾[：:：]\s*', '', md_text, flags=re.MULTILINE)
    md_text = re.sub(r'^金句[：:：]\s*', '', md_text, flags=re.MULTILINE)
    
    # ========== 步骤0.5：保护话题标签的 # 号 ==========
    TAG_HASH = 'HASHTAGPROTECT'
    
    def protect_hash(m):
        return TAG_HASH + m.group(1)
    
    lines = md_text.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^#[\u4e00-\u9fa5a-zA-Z0-9]+(?:\s+#[\u4e00-\u9fa5a-zA-Z0-9]+)*$', stripped):
            protected = re.sub(r'#', TAG_HASH, stripped)
            new_lines.append(protected)
        else:
            new_lines.append(line)
    md_text = '\n'.join(new_lines)
    
    # ========== 步骤1：Markdown 转 HTML ==========
    html = markdown.markdown(md_text, extensions=['nl2br', 'sane_lists', 'fenced_code'])
    
    # ========== 步骤1.5：还原话题标签（无 inline style）==========
    def restore_tag_paragraph(m):
        content_inner = m.group(1)
        content_inner = content_inner.replace(TAG_HASH, '#')
        return '<p>' + content_inner + '</p>'
    
    html = re.sub(
        r'<p>(' + TAG_HASH + r'.*?)</p>',
        restore_tag_paragraph,
        html
    )
    
    # ========== 步骤2：应用样式 ==========
    # H4
    html = re.sub(
        r'<h4>(.*?)</h4>',
        '<h4 style="margin: 1.2em 0 0.6em; font-size: 15px; font-weight: 600; color: ' + colors["heading"] + ';">\\1</h4>',
        html
    )
    # H2（无边框）
    html = re.sub(
        r'<h2>(.*?)</h2>',
        '<h2 style="margin: 1.5em 0 1em; font-size: 20px; font-weight: 600; color: ' + colors["heading"] + ';">\\1</h2>',
        html
    )
    # H3
    html = re.sub(
        r'<h3>(.*?)</h3>',
        '<h3 style="margin: 1.5em 0 0.8em; font-size: 17px; font-weight: 600; color: ' + colors["heading"] + ';">\\1</h3>',
        html
    )
    # 段落：只用字符串替换 <p> 为 <p style=...>（不影响已带 style 的 <p>）
    html = html.replace('<p>', '<p style="margin: 1.2em 0; line-height: 1.9; color: ' + colors["text"] + '; font-size: 16px;">')
    # 加粗
    html = re.sub(
        r'<strong>(.*?)</strong>',
        '<strong style="color: ' + colors["strong"] + '; background: ' + colors["strong_bg"] + '; padding: 2px 6px; border-radius: 3px;">\\1</strong>',
        html
    )
    # 引用块
    html = re.sub(
        r'<blockquote>(.*?)</blockquote>',
        '<blockquote style="border-left: 4px solid ' + colors["quote_border"] + '; background: ' + colors["quote_bg"] + '; color: ' + colors["quote_text"] + '; padding: 1em 1.5em; margin: 1.5em 0; border-radius: 0 8px 8px 0;">\\1</blockquote>',
        html,
        flags=re.DOTALL
    )
    # 列表
    html = re.sub(r'<ul>', '<ul style="padding-left: 2em; line-height: 2.2; color: ' + colors["text"] + ';">', html)
    html = re.sub(r'<ol>', '<ol style="padding-left: 2em; line-height: 2.2; color: ' + colors["text"] + ';">', html)
    
    # ========== 步骤3：包装容器 ==========
    wrapped = ('<section style="background: white; border-radius: 8px; padding: 20px 15px; '
               + 'box-shadow: 0 2px 8px rgba(0,0,0,0.08);">\n' + html + '\n</section>')
    
    return wrapped
