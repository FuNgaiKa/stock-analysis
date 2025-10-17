"""报告和通知 - Reporting and Notification

包含报告生成和通知发送模块
"""

from .report_generator import TextReportGenerator, HTMLReportGenerator
from .chart_generator import ChartGenerator

# 延迟导入，避免在导入时就需要yaml等依赖
# from .daily_market_reporter import DailyMarketReporter
# from .email_notifier import EmailNotifier

__all__ = [
    'TextReportGenerator',
    'HTMLReportGenerator',
    'ChartGenerator',
]
