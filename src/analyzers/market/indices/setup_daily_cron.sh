#!/bin/bash
# 四大科技指数分析 - 每日定时任务安装脚本

echo "========================================"
echo "四大科技指数分析 - 定时任务安装"
echo "========================================"

# 项目路径
PROJECT_DIR="/Users/russ/PycharmProjects/stock-analysis"
SCRIPT_PATH="$PROJECT_DIR/scripts/tech_indices_analysis/run_tech_comprehensive_analysis.py"
LOG_DIR="$PROJECT_DIR/logs"

# 检查脚本是否存在
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 错误: 脚本不存在 $SCRIPT_PATH"
    exit 1
fi

# 创建日志目录
mkdir -p "$LOG_DIR"
echo "✅ 日志目录: $LOG_DIR"

# 检查Python
PYTHON_BIN=$(which python3)
if [ -z "$PYTHON_BIN" ]; then
    echo "❌ 错误: 未找到python3"
    exit 1
fi
echo "✅ Python路径: $PYTHON_BIN"

# 显示当前crontab
echo ""
echo "当前crontab配置:"
echo "----------------------------------------"
crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "(空)"
echo "----------------------------------------"

# cron任务内容
CRON_JOB="0 15 * * * cd $PROJECT_DIR && $PYTHON_BIN $SCRIPT_PATH --email >> $LOG_DIR/tech_analysis.log 2>&1"

echo ""
echo "将添加以下定时任务:"
echo "----------------------------------------"
echo "$CRON_JOB"
echo "----------------------------------------"
echo ""
echo "执行时间: 每天下午3:00"
echo "日志文件: $LOG_DIR/tech_analysis.log"
echo ""

# 询问用户确认
read -p "是否继续安装? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "run_tech_comprehensive_analysis.py"; then
    echo "⚠️  检测到已存在相关定时任务,先删除旧任务..."
    crontab -l 2>/dev/null | grep -v "run_tech_comprehensive_analysis.py" | crontab -
fi

# 添加新任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ 定时任务安装成功!"
echo ""
echo "验证安装:"
echo "----------------------------------------"
crontab -l | grep "run_tech_comprehensive_analysis.py"
echo "----------------------------------------"
echo ""
echo "💡 提示:"
echo "1. 确保已配置 $PROJECT_DIR/config/email_config.yaml"
echo "2. 定时任务将在每天下午3点执行"
echo "3. 查看日志: tail -f $LOG_DIR/tech_analysis.log"
echo "4. 手动测试: $PYTHON_BIN $SCRIPT_PATH --email"
echo ""
echo "如需删除定时任务,请运行:"
echo "  crontab -e"
echo "  然后删除包含 'run_tech_comprehensive_analysis.py' 的行"
echo ""
echo "✨ 安装完成!"
