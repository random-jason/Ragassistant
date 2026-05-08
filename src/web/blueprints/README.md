# Web应用蓝图架构

## 概述

本项目采用Flask蓝图（Blueprint）架构，将原本1953行的单一`app.py`文件重构为多个模块化的蓝图，提高了代码的可维护性和可扩展性。

## 架构改进

### 重构前
- **app.py**: 1953行，包含所有API路由
- 代码混乱，有乱码问题
- 难以维护和扩展
- 单文件过长导致错误

### 重构后
- **app.py**: 674行，只包含核心路由和蓝图注册
- **blueprints/**: 模块化的蓝图目录
  - `alerts.py`: 预警管理相关API
  - `workorders.py`: 工单管理相关API
  - `conversations.py`: 对话管理相关API
  - `knowledge.py`: 知识库管理相关API
  - `monitoring.py`: 监控相关API
  - `system.py`: 系统管理相关API
  - ~~`feishu_sync.py`~~: 已合并到主仪表板（删除）

## 蓝图模块说明

### 1. alerts.py - 预警管理
- `/api/alerts` - 获取预警列表
- `/api/alerts` (POST) - 创建预警
- `/api/alerts/statistics` - 获取预警统计
- `/api/alerts/<id>/resolve` - 解决预警

### 2. workorders.py - 工单管理
- `/api/workorders` - 工单CRUD操作
- `/api/workorders/import` - 工单导入
- `/api/workorders/<id>/ai-suggestion` - AI建议生成
- `/api/workorders/<id>/human-resolution` - 人工解决方案
- `/api/workorders/<id>/approve-to-knowledge` - 审批入库

### 3. conversations.py - 对话管理
- `/api/conversations` - 对话历史管理
- `/api/conversations/<id>` - 对话详情
- `/api/conversations/clear` - 清空对话历史

### 4. knowledge.py - 知识库管理
- `/api/knowledge` - 知识库CRUD操作
- `/api/knowledge/search` - 知识库搜索
- `/api/knowledge/upload` - 文件上传生成知识
- `/api/knowledge/verify` - 知识验证

### 5. monitoring.py - 监控管理
- `/api/token-monitor/*` - Token使用监控
- `/api/ai-monitor/*` - AI性能监控
- 监控数据统计和图表

### 6. system.py - 系统管理
- `/api/settings` - 系统设置
- `/api/system-optimizer/*` - 系统优化
- `/api/backup/*` - 数据备份
- `/api/database/status` - 数据库状态

### 7. 飞书集成功能（已合并）
- **原独立页面**: `http://localhost:5000/feishu-sync`
- **现集成位置**: 主仪表板的"飞书同步"标签页
- **功能**: 飞书多维表格数据同步和管理
- **API端点**: 通过主应用路由提供

## 优势

1. **模块化**: 每个功能模块独立，便于维护
2. **可扩展**: 新增功能只需创建新的蓝图
3. **代码复用**: 蓝图可以在多个应用中复用
4. **团队协作**: 不同开发者可以独立开发不同模块
5. **错误隔离**: 单个模块的错误不会影响整个应用
6. **测试友好**: 可以独立测试每个蓝图模块

## 使用方式

```python
# 注册蓝图
app.register_blueprint(alerts_bp)
app.register_blueprint(workorders_bp)
app.register_blueprint(conversations_bp)
app.register_blueprint(knowledge_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(system_bp)
```

## 文件结构

```
src/web/
├── app.py                 # 主应用文件 (674行)
├── app_backup.py          # 原文件备份
├── blueprints/            # 蓝图目录
│   ├── __init__.py
│   ├── alerts.py          # 预警管理
│   ├── workorders.py      # 工单管理
│   ├── conversations.py   # 对话管理
│   ├── knowledge.py       # 知识库管理
│   ├── monitoring.py      # 监控管理
│   ├── system.py         # 系统管理
│   └── README.md         # 架构说明
├── static/               # 静态文件
│   ├── css/
│   │   └── style.css     # 样式文件（包含飞书集成样式）
│   └── js/
│       ├── dashboard.js  # 仪表板逻辑（包含飞书同步功能）
│       ├── chat.js       # 对话功能
│       └── app.js        # 应用主逻辑
└── templates/            # 模板文件
    ├── dashboard.html    # 主仪表板（包含飞书同步标签页）
    ├── chat.html         # 对话页面
    └── index.html        # 首页
```

## 注意事项

1. 每个蓝图都有独立的URL前缀
2. 蓝图之间通过共享的数据库连接和模型进行数据交互
3. 懒加载模式避免启动时的重复初始化
4. 错误处理统一在蓝图内部进行
5. 保持与原有API接口的兼容性
6. 飞书集成功能已从独立蓝图合并到主仪表板
7. 前端JavaScript类管理不同功能模块（HelpdeskDashboard、FeishuSyncManager等）

## 最新更新 (v1.4.0)

### 功能合并
- **飞书同步页面合并**: 原独立的飞书同步页面已合并到主仪表板
- **统一用户体验**: 所有功能现在都在一个统一的界面中
- **代码优化**: 删除了冗余的蓝图和模板文件

### 架构改进
- **前端模块化**: JavaScript代码按功能模块组织
- **数据库扩展**: 工单表新增12个飞书相关字段
- **字段映射**: 智能映射飞书字段到本地数据库结构
