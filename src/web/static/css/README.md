# AI Helpdesk - 设计系统

## 概述

本设计系统参考了成熟CRM系统（Salesforce、HubSpot、Zendesk）的设计标准，提供统一的字体、颜色、间距和组件规范。

## 文件结构

```
src/web/static/css/
├── design-system.css      # 核心设计系统
├── style.css             # 主样式文件
├── typography-guide.html # 字体和布局指南
└── README.md            # 本文档
```

## 字体系统

### 字体族
- **主字体**：`-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif`
- **等宽字体**：`'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace`

### 字体大小
基于16px基准的rem系统：

| 类名 | 大小 | 用途 |
|------|------|------|
| `.text-xs` | 12px | 辅助信息 |
| `.text-sm` | 14px | 小文本 |
| `.text-base` | 16px | 正文 |
| `.text-lg` | 18px | 大文本 |
| `.text-xl` | 20px | 小标题 |
| `.text-2xl` | 24px | 中标题 |
| `.text-3xl` | 30px | 大标题 |
| `.text-4xl` | 36px | 主标题 |

### 字重
| 类名 | 字重 | 用途 |
|------|------|------|
| `.font-light` | 300 | 辅助信息 |
| `.font-normal` | 400 | 正文 |
| `.font-medium` | 500 | 强调 |
| `.font-semibold` | 600 | 小标题 |
| `.font-bold` | 700 | 标题 |

## 颜色系统

### 主色调
- **主色**：`#2563eb` (蓝色)
- **成功**：`#059669` (绿色)
- **警告**：`#d97706` (橙色)
- **错误**：`#dc2626` (红色)
- **信息**：`#0891b2` (青色)

### 文本颜色
- **主要文本**：`#0f172a` (深灰)
- **次要文本**：`#475569` (中灰)
- **第三级文本**：`#64748b` (浅灰)
- **禁用文本**：`#94a3b8` (极浅灰)

## 间距系统

基于8px网格的间距系统：

| 类名 | 大小 | 用途 |
|------|------|------|
| `.spacing-1` | 4px | 最小间距 |
| `.spacing-2` | 8px | 小间距 |
| `.spacing-3` | 12px | 中小间距 |
| `.spacing-4` | 16px | 中等间距 |
| `.spacing-6` | 24px | 大间距 |
| `.spacing-8` | 32px | 很大间距 |

## 组件系统

### 按钮
```html
<!-- 按钮大小 -->
<button class="btn btn-primary btn-sm">小按钮</button>
<button class="btn btn-primary">普通按钮</button>
<button class="btn btn-primary btn-lg">大按钮</button>

<!-- 按钮样式 -->
<button class="btn btn-primary">主要按钮</button>
<button class="btn btn-secondary">次要按钮</button>
<button class="btn btn-outline-primary">轮廓按钮</button>
```

### 卡片
```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">卡片标题</h3>
    </div>
    <div class="card-body">
        <p>卡片内容</p>
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">操作</button>
    </div>
</div>
```

### 表格
```html
<table class="table">
    <thead>
        <tr>
            <th>列标题</th>
            <th>数据类型</th>
            <th>状态</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>数据</td>
            <td>文本</td>
            <td><span class="badge badge-success">正常</span></td>
        </tr>
    </tbody>
</table>
```

### 分页
```html
<nav>
    <ul class="pagination">
        <li class="page-item"><a class="page-link" href="#">上一页</a></li>
        <li class="page-item active"><a class="page-link" href="#">1</a></li>
        <li class="page-item"><a class="page-link" href="#">2</a></li>
        <li class="page-item"><a class="page-link" href="#">下一页</a></li>
    </ul>
</nav>
```

## 使用规范

### 标题层级
- **页面标题**：H1 (36px, bold)
- **区块标题**：H2 (30px, semibold)
- **卡片标题**：H3 (24px, semibold)
- **表单标题**：H4 (20px, medium)

### 文本规范
- **正文**：16px, normal
- **辅助信息**：14px, normal
- **标签**：12px, medium
- **按钮文字**：14px, medium

### 间距规范
- **卡片内边距**：24px
- **表单元素间距**：16px
- **按钮间距**：8px
- **文本行间距**：1.5

## 响应式设计

### 断点
- **移动端**：< 768px
- **平板端**：768px - 1024px
- **桌面端**：> 1024px

### 移动端适配
- 按钮宽度100%
- 表格字体缩小
- 卡片内边距减少
- 分页按钮适配

## 浏览器支持

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 更新日志

### v1.0.0 (2025-09-22)
- 初始版本
- 基于成熟CRM系统设计标准
- 统一的字体、颜色、间距系统
- 完整的组件库
- 响应式设计支持

## 贡献指南

1. 遵循现有的设计规范
2. 使用CSS变量进行主题定制
3. 保持组件的可复用性
4. 确保响应式兼容性
5. 更新文档和示例

## 联系方式

如有问题或建议，请联系开发团队。
