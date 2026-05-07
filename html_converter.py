# -*- coding: utf-8 -*-
"""Markdown → HTML 样式转换，配合七天主题配色"""
from config import *
import markdown, re

def get_style_for_weekday(weekday):
    return STYLE_THEMES.get(weekday, STYLE_THEMES[0])["colors"]

def markdown_to_html(md_text, weekday):
    colors = get_style_for_weekday(weekday)
    tag_color = colors["tag"]
    tag_span = '<span style="color: ' + tag_color + ';">'
    
    # ========== 步骤1：Markdown 转 HTML ==========
    # 文章用 ## 和 ### 做标题，# 只用于话题标签
    html = markdown.markdown(md_text, extensions=['nl2br', 'sane_lists', 'fenced_code'])
    
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
    # 第一个 H1 → 文章标题（只有当 H1 内容有实质文字时才作为标题）
    h1_matches = list(re.finditer(r'<h1>(.*?)</h1>', html))
    if h1_matches:
        first = h1_matches[0]
        content = first.group(1).strip()
        # 如果第一个 H1 是标签行（只有 #汉字），则不作为标题处理
        if content and not re.match(r'^(?:#[\u4e00-\u9fa5]+\s*)+$', content):
            title_html = ('<h1 style="font-size: 22px; font-weight: bold; color: ' + colors["heading"]
                          + '; text-align: center; margin-bottom: 0.8em; padding-bottom: 0.5em; '
                          + 'border-bottom: 2px solid ' + colors["quote_border"] + ';">'
                          + content + '</h1>')
            html = html[:first.start()] + title_html + html[first.end():]
    # 段落
    html = re.sub(
        r'<p>(.*?)</p>',
        '<p style="margin: 1.2em 0; line-height: 1.9; color: ' + colors["text"] + '; font-size: 16px;">\\1</p>',
        html
    )
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
    
    # ========== 步骤3：话题标签处理 ==========
    # 标签行特征：H1 内容以 # 开头（Markdown 把 "# #健康 #养生" 解析成 H1）
    # 将这种 H1 转为标签段落样式
    
    def fix_h1_tag(m):
        content = m.group(1)
        # 判断是否是标签行（H1 内容以 # 开头）
        if content.startswith('#'):
            # 提取标签（#后紧跟全汉字）
            tags = re.findall(r'#[\u4e00-\u9fa5]+', content)
            if tags:
                colored = ''.join([tag_span + t + '</span>' for t in tags])
                return ('<p style="color: ' + tag_color + '; font-size: 14px; '
                        + 'margin-top: 2em; line-height: 2;">' + colored + '</p>')
        # 不是标签行，返回原样
        return m.group(0)
    
    html = re.sub(r'<h1>(.*?)</h1>', fix_h1_tag, html)
    
    # ========== 步骤4：包装容器 ==========
    wrapped = ('<section style="background: white; border-radius: 8px; padding: 20px 15px; '
               + 'box-shadow: 0 2px 8px rgba(0,0,0,0.08);">\n' + html + '\n</section>')
    
    return wrapped
