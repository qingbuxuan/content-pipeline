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
    
    # 0. 预处理：把 markdown 标题语法（`## xxx`、`### xxx` 等）转成 HTML 标签
    # 这样解析时原始 # 不会被 markdown 吞掉
    md_text = re.sub(r'^(#{1})(\s+)(.+)$',      r'<h1>\3</h1>',      md_text, flags=re.M)
    md_text = re.sub(r'^(#{2})(\s+)(.+)$',      r'<h2>\3</h2>',      md_text, flags=re.M)
    md_text = re.sub(r'^(#{3})(\s+)(.+)$',      r'<h3>\3</h3>',      md_text, flags=re.M)
    md_text = re.sub(r'^(#{4})(\s+)(.+)$',     r'<h4>\3</h4>',      md_text, flags=re.M)
    
    # 1. Markdown 转 HTML（此时标题已是 HTML 标签，不再被解析为语法）
    html = markdown.markdown(md_text, extensions=['nl2br', 'sane_lists', 'fenced_code'])
    
    # 2. 应用样式
    # H4 子子小节标题（h4不会被markdown标准解析器输出，但备用）
    html = re.sub(
        r'<h4>(.*?)</h4>',
        f'<h4 style="margin: 1.2em 0 0.6em; font-size: 15px; font-weight: 600; color: {colors["heading"]};">\\1</h4>',
        html
    )
    
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
    
    # ========== 话题标签处理（重写） ==========
    # 规则：
    #   1. 第一个 H1 → 文章标题（居中大字）
    #   2. 其余 H1 → 标签行（小字标签色，补#）
    #   3. H2/H3 内的 #标签 → 标签色（只着色，不改标签结构）
    #   4. <p> 内的 #标签 → 标签色
    #   5. 文末纯标签行（<p>整行都是#标签）→ 标签段落样式
    #   6. 绝不修改不含#的正常段落

    # A. H1 处理：第一个为标题，其余为标签行
    h1_count = [0]
    def fix_h1_tag(m):
        content = m.group(1).strip()
        h1_count[0] += 1
        if h1_count[0] == 1:
            return f'<h1 style="font-size: 22px; font-weight: bold; color: {colors["heading"]}; text-align: center; margin-bottom: 0.8em; padding-bottom: 0.5em; border-bottom: 2px solid {colors["quote_border"]};">' + content + '</h1>'
        else:
            if re.match(r'^[\u4e00-\u9fa5a-zA-Z]', content) and not content.startswith('#'):
                content = '#' + content
            return f'<p style="color: {colors["tag"]}; font-size: 14px; margin-top: 2em; line-height: 2;">' + content + '</p>'
    html = re.sub(r'<h1>([\s\S]*?)</h1>', fix_h1_tag, html)

    # B. H2/H3 内的 #标签 → 标签色（只着色，不改标签结构）
    def color_hash_in_heading(tag_name):
        def replacer(m):
            inner = m.group(1)
            # 给 #中文/英文 标签上色
            colored = re.sub(
                r'(#[\u4e00-\u9fa5a-zA-Z]\w*)',
                f'<span style="color: {colors["tag"]}; font-size: 0.75em;">\\1</span>',
                inner
            )
            if colored == inner:
                return m.group(0)  # 没有#标签，原样返回
            return f'<{tag_name}{m.group(2)}>{colored}</{tag_name}>'
        return replacer
    html = re.sub(r'<h2([^>]*)>(.*?)</h2>', color_hash_in_heading('h2'), html, flags=re.DOTALL)
    html = re.sub(r'<h3([^>]*)>(.*?)</h3>', color_hash_in_heading('h3'), html, flags=re.DOTALL)

    # C. <p> 内的 #标签着色（支持带 style 属性的 <p>）
    # 匹配 <p...>#标签...</p> 的各种格式
    tag_color = colors['tag']
    tag_span = f'<span style="color: {tag_color}; font-size: 14px;">'

    # C1. 整个 <p> 内容都是 #标签（纯标签行）
    def fix_pure_tag_line(m):
        content = m.group(1).strip()
        # 确认内容确实全是 #标签（至少含一个#标签，其余也是#标签或空格）
        if not re.match(r'^#[\u4e00-\u9fa5a-zA-Z]', content):
            return m.group(0)  # 不以#标签开头，原样返回
        return f'<p style="color: {tag_color}; font-size: 14px; margin-top: 2em; line-height: 2;">' + content + '</p>'
    html = re.sub(r'<p[^>]*>((?:\s*#[\u4e00-\u9fa5a-zA-Z][\u4e00-\u9fa5\w]*(?:\s+|\s*</p>))+)', fix_pure_tag_line, html)

    # C2. <p> 内中间/末尾的 #标签着色（不影响不含#的正常段落）
    def color_tag_in_p(m):
        inner = m.group(2)
        if '#' not in inner:
            return m.group(0)  # 无#，原样返回
        # 只给 #标签 上色
        colored = re.sub(
            r'(#[\u4e00-\u9fa5a-zA-Z][\u4e00-\u9fa5\w]*)',
            tag_span + r'\1</span>',
            inner
        )
        if colored == inner:
            return m.group(0)  # 没有#标签被着色
        return f'<p{m.group(1)}>{colored}</p>'
    html = re.sub(r'<p([^>]*)>(.*?)</p>', color_tag_in_p, html, flags=re.DOTALL)
    
    # 包装在白色卡片容器中
    wrapped_html = f'''<section style="background: white; border-radius: 8px; padding: 20px 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
{html}
</section>'''
    
    return wrapped_html
