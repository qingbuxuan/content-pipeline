# -*- coding: utf-8 -*-
"""Markdown → HTML 样式转换，配合七天主题配色"""
from config import *
import markdown, re

def get_style_for_weekday(weekday):
    """获取当天主题的样式配色"""
    return STYLE_THEMES.get(weekday, STYLE_THEMES[0])["colors"]

def markdown_to_html(md_text, weekday):
    """Markdown 转 HTML，应用当天主题样式"""
    colors = get_style_for_weekday(weekday)
    
    # 1. Markdown 转 HTML
    html = markdown.markdown(md_text, extensions=['nl2br', 'sane_lists', 'fenced_code'])
    
    # 2. 应用样式
    # H2 大章节标题
    html = re.sub(
        r'<h2>(.*?)</h2>',
        f'<h2 style="margin: 1.5em 0 1em; padding-left: 15px; border-left: 4px solid {colors["primary"]}; font-size: 20px; font-weight: 600; color: {colors["heading"]};">\\1</h2>',
        html
    )
    
    # H3 子小节标题
    html = re.sub(
        r'<h3>(.*?)</h3>',
        f'<h3 style="margin: 1.5em 0 0.8em; font-size: 17px; font-weight: 600; color: {colors["heading"]};">\\1</h3>',
        html
    )
    
    # 段落
    html = re.sub(
        r'<p>(.*?)</p>',
        f'<p style="margin: 1.2em 0; line-height: 1.9; color: {colors["text"]}; font-size: 16px;">\\1</p>',
        html
    )
    
    # 重点加粗
    html = re.sub(
        r'<strong>(.*?)</strong>',
        f'<strong style="color: {colors["strong"]}; background: {colors["strong_bg"]}; padding: 2px 6px; border-radius: 3px;">\\1</strong>',
        html
    )
    
    # 引用块
    html = re.sub(
        r'<blockquote>(.*?)</blockquote>',
        f'<blockquote style="border-left: 4px solid {colors["quote_border"]}; background: {colors["quote_bg"]}; color: {colors["quote_text"]}; padding: 1em 1.5em; margin: 1.5em 0; border-radius: 0 8px 8px 0;">\\1</blockquote>',
        html,
        flags=re.DOTALL
    )
    
    # 列表
    html = re.sub(
        r'<ul>',
        f'<ul style="padding-left: 2em; line-height: 2.2; color: {colors["text"]};">',
        html
    )
    html = re.sub(
        r'<ol>',
        f'<ol style="padding-left: 2em; line-height: 2.2; color: {colors["text"]};">',
        html
    )
    
    # 处理话题标签（#话题标签），匹配各种可能性：
    # - 行首标签: <p>#健康 #养生</p>
    # - 行中标签: <p>aaa #健康 #养生</p>
    # - 分割线后标签块: ### ###标签块
    # 统一加样式，原始 # 保留（前端显示）
    for ptn, tag in [
        (r'(<p([^>]*)>)(#[^<]+)(</p>)', r'\1<span style="color: ' + colors['tag'] + r'; font-size: 14px;"' + r'>\3</span>\4'),
        (r'(<p([^>]*)>[^<]*)(#[\u4e00-\u9fa5\w]+)(</p>)', r'\1<span style="color: ' + colors['tag'] + r'; font-size: 14px;">' + r'\3</span>\4'),
    ]:
        html = re.sub(ptn, tag, html)
    # 文末纯标签行：<p>#健康 #养生</p> 这种整行都是标签的，做大字体处理
    # 匹配整个p内容都是#开头的标签的情况
    tag_only = r'(<p([^>]*)>\s*)(#[^<#]+(?:\s+#[^<#]+)*)(\s*</p>)'
    html = re.sub(
        tag_only,
        lambda m: m.group(1) + '<span style="color: ' + colors['tag'] + r'; font-size: 14px; line-height: 2;">' + m.group(3).strip() + '</span>' + m.group(4),
        html
    )
    html = re.sub(
        r'<p style="[^"]*">((?:\s*#(?:[\u4e00-\u9fa5\w])+)+)(?:\s*</p>)',
        lambda m: '<p style="color: ' + colors['tag'] + r'; font-size: 14px; margin-top: 2em; line-height: 2;">' + m.group(1).strip() + '</p>',
        html
    )
    
    # 包装在白色卡片容器中
    wrapped_html = f'''<section style="background: white; border-radius: 8px; padding: 20px 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
{html}
</section>'''
    
    return wrapped_html
