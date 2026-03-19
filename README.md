# 🚀 全自动短视频变现系统

基于AI的短视频内容生产到变现的完整自动化解决方案。

## 📋 系统架构

```
GitHub Actions 定时调度
        │
        ├── 06:00 ──▶ 热点自动抓取机器人
        ├── 07:00 ──▶ AI脚本批量生成机器人  
        ├── 08:00 ──▶ 数据监控日报推送
        └── 每小时 ──▶ 系统健康检查
```

## 🛠️ 技术栈

| 组件 | 技术方案 | 成本 |
|------|----------|------|
| **调度系统** | GitHub Actions | 免费 |
| **AI模型** | DeepSeek API | ¥0.001/千tokens |
| **数据存储** | 飞书多维表格 | 免费 |
| **消息通知** | 飞书Webhook | 免费 |

## 💰 月度成本

| 项目 | 费用 | 说明 |
|------|------|------|
| DeepSeek API | ¥10-30 | 脚本生成 |
| 一帧秒创API | ¥100-200 | 视频制作（可选） |
| **合计** | **¥10-230** | 全自动运行 |

## 🚀 快速开始

### 第一步：Fork本项目

1. 点击右上角 `Fork` 按钮，将项目复制到您的GitHub账号
2. 等待Fork完成，进入您的项目页面

### 第二步：配置API密钥

进入项目 `Settings` → `Secrets and variables` → `Actions`，添加以下Secrets：

#### 必需配置

| Secret名称 | 获取方式 | 说明 |
|------------|----------|------|
| `DEEPSEEK_API_KEY` | [DeepSeek平台](https://platform.deepseek.com) | AI脚本生成 |
| `FEISHU_APP_ID` | [飞书开放平台](https://open.feishu.cn/app) | 飞书应用ID |
| `FEISHU_APP_SECRET` | 同上 | 飞书应用密钥 |
| `FEISHU_APP_TOKEN` | 飞书多维表格URL中获取 | 表格App Token |
| `FEISHU_TABLE_ID` | 同上 | 表格ID |
| `FEISHU_WEBHOOK` | 飞书群机器人 | 通知Webhook |

#### 可选配置

| Secret名称 | 获取方式 | 说明 |
|------------|----------|------|
| `SILICON_API_KEY` | [硅基流动](https://siliconflow.cn) | DeepSeek备用API |
| `YIZHEN_API_KEY` | [一帧秒创](https://aigc.yizhen.cn) | 视频制作API |

### 第三步：创建飞书表格

1. 在飞书创建一个新的多维表格
2. 添加以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 标题 | 文本 | 热点标题 |
| 热度值 | 数字 | 热度数值 |
| 来源平台 | 文本 | 抖音/微博/知乎 |
| 链接 | 文本 | 原始链接 |
| 匹配关键词 | 文本 | 匹配的关键词 |
| 匹配分数 | 数字 | 匹配关键词数量 |
| 抓取时间 | 日期时间 | 抓取时间 |
| 处理状态 | 单选 | 待审核/脚本已生成/已发布/已忽略 |
| 脚本标题 | 文本 | 生成的脚本标题 |
| 脚本内容 | 文本 | 完整脚本内容 |
| 标签 | 文本 | 视频标签 |
| 生成时间 | 日期时间 | 脚本生成时间 |

3. 获取 `App Token` 和 `Table ID`：
   - 打开表格，复制URL
   - URL格式：`https://example.feishu.cn/base/{AppToken}?table={TableId}`
   - 提取 `AppToken` 和 `TableId`

### 第四步：配置飞书机器人

1. 在飞书群中添加自定义机器人
2. 复制Webhook地址
3. 添加到Secrets中的 `FEISHU_WEBHOOK`

### 第五步：手动测试运行

1. 进入项目 `Actions` 标签页
2. 选择 `Auto Short Video Pipeline`
3. 点击 `Run workflow`
4. 选择要测试的任务（建议先测试 `crawl-hotspots`）
5. 等待运行完成，检查飞书表格是否有数据

### 第六步：启用自动调度

工作流已配置定时任务，无需额外操作：
- 每天6:00：自动抓取热点
- 每天7:00：自动生成脚本
- 每天8:00：自动发送日报

## 📁 项目结构

```
auto-short-video/
├── .github/
│   └── workflows/
│       └── auto-short-video.yml    # GitHub Actions工作流
├── scripts/
│   ├── hot_spot_crawler.py         # 热点抓取脚本
│   ├── script_generator.py         # AI脚本生成脚本
│   ├── video_producer.py           # 视频制作脚本（可选）
│   ├── publish_manager.py          # 发布管理脚本（可选）
│   └── data_monitor.py             # 数据监控脚本
├── config/
│   └── settings.py                 # 系统配置
├── data/                           # 数据存储目录
├── requirements.txt                # Python依赖
└── README.md                       # 项目说明
```

## ⚙️ 自定义配置

编辑 `config/settings.py` 修改系统配置：

### 修改关键词
```python
HOTSPOT_CONFIG['keywords'] = [
    '您的关键词1', '您的关键词2', ...
]
```

### 修改每日生成数量
```python
SCRIPT_CONFIG['daily_limit'] = 20  # 默认10条
```

### 修改发布时间
```python
PUBLISH_CONFIG['schedule'] = [
    '07:00', '12:00', '18:00', '21:00'
]
```

## 📊 日常运营

### 每天您需要做的：

1. **查看飞书日报**（8:00自动推送）
   - 了解昨日数据表现
   - 查看异常预警

2. **审核脚本**（10分钟）
   - 打开飞书表格
   - 查看"脚本已生成"状态的记录
   - 确认可制作视频的脚本

3. **制作视频**（可选，可继续自动化）
   - 使用剪映/一帧秒创制作视频
   - 或使用自动化视频制作（需配置一帧秒创API）

4. **发布视频**
   - 手动发布到各平台
   - 或使用RPA自动发布（需配置影刀RPA）

### 系统会自动做的：

- ✅ 每天抓取热点
- ✅ 每天生成脚本
- ✅ 每天发送日报
- ✅ 数据自动记录
- ✅ 异常自动预警

## 🔧 故障排查

### 热点抓取失败

1. 检查网络连接
2. 检查目标平台是否更新API
3. 查看Actions日志获取详细错误信息

### 脚本生成失败

1. 检查 `DEEPSEEK_API_KEY` 是否正确
2. 检查API余额是否充足
3. 查看DeepSeek平台状态

### 飞书推送失败

1. 检查 `FEISHU_WEBHOOK` 是否正确
2. 检查飞书机器人是否被删除
3. 检查网络连接

## 📈 进阶配置

### 接入视频制作自动化

1. 注册一帧秒创账号
2. 获取API Key
3. 添加到Secrets中的 `YIZHEN_API_KEY`
4. 启用 `video_producer.py` 工作流

### 接入多平台发布

1. 注册影刀RPA
2. 配置各平台账号Cookie
3. 添加到Secrets
4. 启用发布工作流

### 接入支付数据

1. 配置虎皮椒API回调
2. 在 `data_monitor.py` 中添加GMV数据抓取
3. 实现自动对账

## 📝 更新日志

### v1.0.0 (2024-01-15)
- ✅ 热点自动抓取（抖音、微博、知乎）
- ✅ AI脚本批量生成（DeepSeek API）
- ✅ 数据自动监控与日报推送
- ✅ GitHub Actions定时调度
- ✅ 飞书表格数据存储

## 🤝 贡献指南

欢迎提交Issue和PR！

## 📄 许可证

MIT License

## 💬 联系方式

如有问题，请通过以下方式联系：
- 提交GitHub Issue
- 飞书群讨论

---

**🎉 恭喜！现在您拥有了一个7×24小时运行的AI数字员工团队！**
