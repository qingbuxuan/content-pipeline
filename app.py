from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

# 自动生成文章内容
TITLE = "健康养生"
CONTENT = """
<p>1. 早睡早起，保持充足睡眠</p>
<p>2. 饮食清淡，少油少盐</p>
<p>3. 适度运动，增强免疫力</p>
<p>这是自动化生成的文章，直接进入公众号草稿箱。</p>
"""

# 🔥 核心页面：自动调用微信JS，打开草稿并填充内容
@app.route('/trigger')
def trigger():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>自动创建公众号草稿</title>
    </head>
    <body>
        <h3>正在自动跳转到公众号草稿箱...</h3>
        <script>
            // 微信官方图文编辑页（自动创建新草稿）
            const title = "{{ title }}";
            const content = "{{ content }}";
            
            // 拼接带内容的官方编辑链接（直接填充进草稿）
            const url = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=10&lang=zh_CN"
                      + "&title=" + encodeURIComponent(title)
                      + "&content=" + encodeURIComponent(content);
            
            // 直接跳转 = 直接进入草稿编辑页
            window.location.href = url;
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, title=TITLE, content=CONTENT)

@app.route("/")
def index():
    return "✅ 服务运行正常 | 访问 /trigger 自动创建公众号草稿"

# 新增：处理微信域名校验文件（无冲突版本）
@app.route('/MP_verify_<string:filename>.txt')
def verify_file(filename):
    # 把下载的校验文件内容直接写在这里（替换成你实际下载的文件内容）
    # 例如：如果文件内容是 "abc123456789"，就 return "abc123456789"
    return "rbycC54eWHXTLryw"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)