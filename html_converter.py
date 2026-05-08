# -*- coding: utf-8 -*-
"""Markdown → HTML 样式转换，配合七天主题配色"""
from config import *
import markdown, re

def get_style_for_weekday(weekday):
    return STYLE_THEMES.get(weekday, STYLE_THEMES[0])["colors"]

def markdown_to_html(md_text, weekday):
    colors = get_style_for_weekday(weekday)
    tag_color = colors["tag"]
    
    # ========== 步骤0：清洗常见标签前缀 ==========
    # DeepSeek有时会输出"金句收尾："等前缀，自动去掉
    md_text = re.sub(r'^金句收尾[：:：]\s*', '', md_text, flags=re.MULTILINE)
    md_text = re.sub(r'^金句[：:：]\s*', '', md_text, flags=re.MULTILINE)
    
    # ========== 步骤0.5：保护话题标签的 # 号 ==========
    # 微信公众号需要纯文本 #话题标签 才能自动识别为蓝色可点击标签
    # 必须在 Markdown 解析前保护 #，否则 Python-Markdown 会把 #健康 解析为 H1
    #
    # 策略：将话题标签行的 # 替换为占位符，让 Markdown 不识别为标题
    # 解析后再把占位符还原为 #，并给标签行加微信可识别的样式
    
    TAG_HASH = 'HASHTAGPROTECT'
    
    # 匹配：整行都是话题标签（#后紧跟汉字/字母/数字，空格分隔多个标签）
    # 例如：#养生 #健康生活 #中年人
    # 不匹配：# 标题（#后有空格）、## 标题、### 标题
    # 只替换行首的 #（即话题标签的 #），保留行内 # 不动
    
    def protect_hash(m):
        return TAG_HASH + m.group(1)
    
    # 逐行处理：找到整行都是话题标签的行，替换其中的 #
    lines = md_text.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # 检测：整行是否全是话题标签（#汉字/字母/数字 空格分隔）
        if re.match(r'^#[\u4e00-\u9fa5a-zA-Z0-9]+(?:\s+#[\u4e00-\u9fa5a-zA-Z0-9]+)*$', stripped):
            # 替换所有 # 为占位符
            protected = re.sub(r'#', TAG_HASH, stripped)
            new_lines.append(protected)
        else:
            new_lines.append(line)
    md_text = '\n'.join(new_lines)
    
    # ========== 步骤1：Markdown 转 HTML ==========
    html = markdown.markdown(md_text, extensions=['nl2br', 'sane_lists', 'fenced_code'])
    
    # ========== 步骤1.5：还原话题标签 ==========
    # 找到包含占位符的 <p> 元素，还原 # 并加微信可识别样式
    # 微信 API 需要纯文本 #话题标签（不包裹在 span 中）才能自动识别为蓝色可点击标签
    def restore_tag_paragraph(m):
        content = m.group(1)
        # 还原占位符为 #
        content = content.replace(TAG_HASH, '#')
        return ('<p style="color: ' + tag_color + '; font-size: 14px; '
                + 'margin-top: 2em; line-height: 2;">' + content + '</p>')
    
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
    # 段落（匹配无 style 的 <p>，不会匹配已有 style 的话题标签段落）
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
    
    # ========== 步骤3：包装容器 ==========
    wrapped = ('<section style="background: white; border-radius: 8px; padding: 20px 15px; '
               + 'box-shadow: 0 2px 8px rgba(0,0,0,0.08);">\n' + html + '\n</section>')
    
    return wrapped
