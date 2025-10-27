#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML格式化器
HTML Formatter

将Markdown报告转换为精美的HTML格式
"""

import markdown
from pathlib import Path
from datetime import datetime


class HTMLFormatter:
    """HTML报告格式化器"""

    def __init__(self):
        """初始化HTML格式化器"""
        # Markdown扩展
        self.md_extensions = [
            'tables',           # 表格支持
            'fenced_code',      # 代码块
            'nl2br',            # 换行转<br>
            'sane_lists',       # 更好的列表
            'codehilite',       # 代码高亮
            'toc',              # 目录
        ]

        # CSS样式
        self.css_style = """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f7fa;
                padding: 20px;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }

            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
                font-size: 2.2em;
            }

            h2 {
                color: #34495e;
                margin-top: 40px;
                margin-bottom: 20px;
                padding-left: 10px;
                border-left: 4px solid #3498db;
                font-size: 1.8em;
            }

            h3 {
                color: #546e7a;
                margin-top: 25px;
                margin-bottom: 15px;
                font-size: 1.4em;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }

            td {
                padding: 10px 12px;
                border-bottom: 1px solid #ecf0f1;
            }

            tr:hover {
                background: #f8f9fa;
            }

            /* 状态标签样式 */
            td:contains("✅") {
                color: #27ae60;
            }

            td:contains("🚨"), td:contains("⚠️") {
                color: #e74c3c;
                font-weight: 600;
            }

            /* 代码块样式 */
            pre, code {
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 0.9em;
            }

            code {
                padding: 2px 6px;
                font-size: 0.9em;
            }

            /* 列表样式 */
            ul, ol {
                margin-left: 30px;
                margin-bottom: 15px;
            }

            li {
                margin-bottom: 8px;
            }

            /* 分隔线 */
            hr {
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 40px 0;
            }

            /* 强调文本 */
            strong {
                color: #2c3e50;
                font-weight: 600;
            }

            /* 引用块 */
            blockquote {
                border-left: 4px solid #3498db;
                padding-left: 20px;
                margin: 20px 0;
                color: #7f8c8d;
                font-style: italic;
            }

            /* 警告框 */
            .alert {
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }

            .alert-danger {
                background: #fee;
                border-left: 4px solid #e74c3c;
            }

            .alert-warning {
                background: #fffbea;
                border-left: 4px solid #f39c12;
            }

            .alert-success {
                background: #e8f5e9;
                border-left: 4px solid #27ae60;
            }

            .alert-info {
                background: #e3f2fd;
                border-left: 4px solid #3498db;
            }

            /* 页脚 */
            .footer {
                margin-top: 50px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
                text-align: center;
                color: #95a5a6;
                font-size: 0.9em;
            }

            /* 打印样式 */
            @media print {
                body {
                    background: white;
                }

                .container {
                    box-shadow: none;
                    padding: 20px;
                }

                .no-print {
                    display: none;
                }
            }
        </style>
        """

    def markdown_to_html(
        self,
        markdown_content: str,
        title: str = "持仓调整策略报告"
    ) -> str:
        """
        将Markdown转换为HTML

        Args:
            markdown_content: Markdown内容
            title: 页面标题

        Returns:
            完整的HTML文档
        """
        # 转换Markdown
        html_body = markdown.markdown(
            markdown_content,
            extensions=self.md_extensions
        )

        # 生成完整HTML
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="Claude Code Quant System v2.0">
    <title>{title}</title>
    {self.css_style}
</head>
<body>
    <div class="container">
        {html_body}

        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>由 <strong>Claude Code 机构级量化系统 v2.0</strong> 生成</p>
        </div>
    </div>
</body>
</html>
"""
        return html_template

    def save_html(
        self,
        markdown_content: str,
        output_path: str,
        title: str = "持仓调整策略报告"
    ) -> None:
        """
        保存为HTML文件

        Args:
            markdown_content: Markdown内容
            output_path: 输出路径
            title: 页面标题
        """
        html_content = self.markdown_to_html(markdown_content, title)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


if __name__ == '__main__':
    # 测试HTML格式化
    formatter = HTMLFormatter()

    test_markdown = """
# 测试报告

## 第一章节

这是一个测试。

### 表格测试

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| ✅ 正常 | 100 | 良好 |
| ⚠️ 警告 | 50 | 注意 |
| 🚨 危险 | 10 | 紧急 |

### 列表测试

- 项目1
- 项目2
- 项目3

### 代码测试

```python
def test():
    print("Hello, World!")
```

---

**结束**
    """

    html = formatter.markdown_to_html(test_markdown, "测试报告")
    formatter.save_html(test_markdown, "test_report.html", "测试报告")

    print("HTML格式化器测试完成!")
    print("已生成: test_report.html")
