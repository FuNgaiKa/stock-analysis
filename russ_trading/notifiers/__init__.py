#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模块

包含邮件等通知功能:
- UnifiedEmailNotifier: 统一邮件通知器
"""

from .unified_email_notifier import UnifiedEmailNotifier

__all__ = [
    'UnifiedEmailNotifier',
]
