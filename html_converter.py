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
    # H2 大章节标题（纯文本样式，无边框）
    html = re.sub(
        r'<h2>(.*?)</h2>',
        f'<h2 style="margin: 1.5em 0 1em; font-size: 20px; font-weight: 600; color: {colors["heading"]};">\\1</h2>',
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
    
    # 处理话题标签（#话题标签），Markdown会把单独一行的 `#标签` 解析成 h1，此时第一个 # 被标题语法消耗掉
    # 1. 处理 h1 误判：被误判为标题的标签行，h1内容是 `健康 #养生`（没有开头的#），需补上#
    def fix_h1_tag(m):
        content = m.group(1).strip()
        # 如果内容以标签字符（中文/英文）开头但没有 #，说明#被标题语法消耗了，补上
        if re.match(r'^[\u4e00-\u9fa5a-zA-Z]', content) and not content.startswith('#'):
            content = '#' + content
        return f'<p style="color: {colors["tag"]}; font-size: 14px; margin-top: 2em; line-height: 2;">' + content + '</p>'
    html = re.sub(r'<h1>\s*([\s\S]*?)\s*</h1>', fix_h1_tag, html)
    
    # 2. 处理普通 p 段落中的标签
    for ptn, tag in [
        (r'(<p([^>]*)>)(#[^<]+)(</p>)', r'\1<span style="color: ' + colors['tag'] + r'; font-size: 14px;"' + r'>\3</span>\4'),
        (r'(<p([^>]*)>[^<]*)(#[\u4e00-\u9fa5\w]+)(</p>)', r'\1<span style="color: ' + colors['tag'] + r'; font-size: 14px;">' + r'\3</span>\4'),
    ]:
        html = re.sub(ptn, tag, html)
    
    # 3. 文末纯标签行：整个p都是标签，补上可能缺失的#
    def fix_tag_only(m):
        content = m.group(3).strip()
        if re.match(r'^[\u4e00-\u9fa5a-zA-Z]', content) and not content.startswith('#'):
            content = '#' + content
        return m.group(1) + '<span style="color: ' + colors['tag'] + r'; font-size: 14px; line-height: 2;">' + content + '</span>' + m.group(4)
    tag_only = r'(<p([^>]*)>\s*)([\S\s]*?)(\s*</p>)'
    html = re.sub(tag_only, fix_tag_only, html)
    
    # 4. 最后兜底：处理 <p>#标签...</p> 这种格式
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
