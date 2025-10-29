#!/bin/bash
# 清理已提交的敏感报告文件

echo "🔒 开始清理敏感报告文件..."

# 从git历史中移除敏感报告（保留目录结构）
git filter-branch --force --index-filter \
  "git rm -rf --cached --ignore-unmatch \
    'reports/daily/2025-10/*.md' \
    'reports/daily/2025/*.md' \
    'reports/monthly/*.md' \
    'reports/archive/russ_*.md' \
    'reports/archive/comprehensive_asset_*.md'" \
  --prune-empty --tag-name-filter cat -- --all

echo "✅ 已从 git 历史移除敏感报告"
echo ""
echo "⚠️  注意：需要强制推送才能更新远程仓库："
echo "   git push origin --force --all"
echo ""
echo "💡 建议：先备份本地文件，确认无误后再推送"
