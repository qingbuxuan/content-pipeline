# 微信公众号健康内容流水线

自动化生成 + 推送健康养生类公众号文章，支持**七天主题循环**。

## 系统架构

```
触发（cron-job / UptimeRobot ping）
  ↓
content-pipeline/app.py
  ├── node1_collector  → 采集热榜话题
  ├── node2_title      → DeepSeek 生成标题（5选1）
  ├── node3_outline    → 生成大纲
  ├── node4_article    → 生成正文（含防重复逻辑）
  ├── node5_summary_and_cover → 生成摘要 + 通义万相封面图
  └── node6_send       → 推送飞书记录 + 微信草稿箱
```

## 七天主题系统

| 星期 | 主题 | 颜色主调 | 话题方向 |
|------|------|----------|----------|
| 周一 | 情感心理 | 粉红 #e91e63 | 空巢孤独、代际沟通 |
| 周二 | 养生生活 | 绿色 #4caf50 | 四季养生、药食同源 |
| 周三 | 慢病管理 | 橙色 #ff9800 | 三高、糖尿病、用药 |
| 周四 | 情绪养生 | 紫色 #9c27b0 | 焦虑抑郁、失眠心理 |
| 周五 | 生活品质 | 蓝色 #2196f3 | 消费避坑、保健品 |
| 周六 | 科技健康 | 青色 #00bcd4 | 智能设备、健康APP |
| 周日 | 科普急救 | 红色 #f44336 | 心梗急救、家庭药箱 |

## 核心流程（6步）

1. **采集** — 爬取百度/微博/头条热榜，按当天主题关键词过滤打分
2. **标题** — DeepSeek 三把钩子法生成 5 个标题，择优使用
3. **大纲** — 三把钩子结构（开头钩+中间信任+结尾行动）
4. **正文** — 1200-1500字，含 12 要素自检，口语化去 AI 味
5. **摘要+封面** — 80-90字摘要 + 通义万相生成 1280×720 封面图
6. **推送** — 写入飞书多维表格 + 推送微信草稿箱

## 三把钩子写作法

- **第一把钩子（开头）**：目标读者画像 + 扎心问题 + 痛点场景 + 好处承诺
- **第二把钩子（中间）**：核心观点 + 真实例子 + 底层逻辑（"其实……"开头）
- **第三把钩子（结尾）**：可操作步骤 + 亲身经历 + 金句收尾 + 互动提问

## 防重复机制

`read_articles(weekday, limit=4)` 从飞书多维表格读取最近 4 周同主题正文，
注入 `node4_article` prompt，让 DeepSeek 避免重复选题角度。

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `SERVERCHAN_KEY` | Server酱 SendKey，推送微信通知 |
| `DEEPSEEK_API_KEY` | DeepSeek API，生成文章内容 |
| `WANXIANG_AI_KEY` | 通义万相 API，生成封面图 |
| `WX_APPID` | 微信公众号 AppID |
| `WX_APPSECRET` | 微信公众号 AppSecret |
| `FEISHU_APP_ID` | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret |
| `FEISHU_BITABLE_TOKEN` | 飞书多维表格 Token |
| `FEISHU_ARTICLES_TABLE_ID` | 飞书文章记录表 ID |

## API Endpoints

| 路由 | 说明 |
|------|------|
| `GET /` | 健康检查 + 版本信息 |
| `GET /trigger?force=1` | 手动触发完整流水线 |
| `GET /status` | 查看上次执行状态 |

## 部署

- **平台**：Render（自动部署 from GitHub）
- **入口**：`gunicorn app:app --bind 0.0.0.0:$PORT`
- **保活**：UptimeRobot 每 5 分钟 ping 一次
- **定时**：cron-job.org 每天北京时间 6:00 触发
- **防重复**：每日锁文件（`executed_YYYYMMDD.lock`）防止同一自然日重复执行

## 文件结构

```
content-pipeline/
├── app.py              # 主程序（含所有节点 + Flask 路由）
├── .env                 # 本地环境变量（不上传）
├── .gitignore           # 忽略 .env
├── requirements.txt     # 依赖包
├── LICENSE              # CC BY-NC 4.0
└── README.md            # 本文档
```

## 技术栈

- **语言**：Python 3
- **Web 框架**：Flask + Gunicorn
- **AI**：DeepSeek Chat API（文章生成）
- **绘图**：通义万相（封面图）
- **数据**：飞书多维表格（历史记录）
- **部署**：Render + cron-job.org
- **消息**：Server酱（微信通知）