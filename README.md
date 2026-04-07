# 内容生产流水线

一个基于 AI 的自动化内容生产系统，支持多源热榜采集、智能选题、文章生成、封面图生成、多渠道推送。

## 功能特性

- 🔥 **多源热榜采集**：百度热搜 + 微博热搜 + 今日头条
- 🎯 **智能选题**：7天主题系统 + 关键词分级权重
- ✍️ **AI 写作**：DeepSeek 驱动的"三把钩子"爆款写作法
- 🖼️ **封面生成**：通义万相 AI 绘图
- 📤 **多渠道推送**：Server酱 + 微信公众号草稿箱
- ⏰ **定时执行**：支持 cron 定时任务

## 技术栈

- Python 3.10+
- Flask
- DeepSeek API
- 通义万相 API
- Server酱
- 微信公众平台 API

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/qingbuxuan/content-pipeline.git
cd content-pipeline
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

需要配置的环境变量：

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| `SERVERCHAN_KEY` | Server酱推送密钥 | https://sct.ftqq.com |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | https://platform.deepseek.com |
| `WANXIANG_API_KEY` | 通义万相 API 密钥 | https://dashscope.aliyun.com |
| `WX_APPID` | 微信公众号 AppID（可选） | 微信公众平台 |
| `WX_APPSECRET` | 微信公众号 AppSecret（可选） | 微信公众平台 |

### 4. 运行

```bash
python app.py
```

访问 http://localhost:5000 查看状态。

## 7天主题系统

| 星期 | 主题 | 方向 |
|------|------|------|
| 周一 | 情感心理 | 空巢孤独、代际沟通 |
| 周二 | 养生生活 | 四季养生、食疗药膳 |
| 周三 | 慢病管理 | 三高、糖尿病用药 |
| 周四 | 情绪养生 | 焦虑抑郁、心理健康 |
| 周五 | 生活品质 | 消费避坑、保健品测评 |
| 周六 | 科技健康 | 智能设备、健康APP |
| 周日 | 科普急救 | 心梗急救、家庭药箱 |

## 部署

推荐使用 [Render](https://render.com) 部署：

1. Fork 本仓库
2. 在 Render 创建 Web Service
3. 连接 GitHub 仓库
4. 配置环境变量
5. 部署

## 许可协议

[CC BY-NC 4.0](LICENSE) - 禁止商用

✅ 可以学习、参考、二次开发（个人/教育用途）
❌ 禁止商用（付费课程、付费服务、商业产品）

## 致谢

- [DeepSeek](https://deepseek.com) - AI 写作
- [通义万相](https://dashscope.aliyun.com) - AI 绘图
- [Server酱](https://sct.ftqq.com) - 微信推送
