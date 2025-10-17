#!/bin/bash
# 综合资产分析定时任务安装脚本
# 用途: 设置每日自动运行综合资产分析并发送邮件

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/Users/russ/PycharmProjects/stock-analysis"
PYTHON_BIN="/usr/bin/python3"
SCRIPT_PATH="${PROJECT_ROOT}/scripts/comprehensive_asset_analysis/run_asset_analysis.py"
LOG_DIR="${PROJECT_ROOT}/logs"

echo "========================================="
echo "综合资产分析定时任务安装"
echo "========================================="

# 检查Python
if [ ! -f "$PYTHON_BIN" ]; then
    echo -e "${RED}❌ Python3未找到: $PYTHON_BIN${NC}"
    echo "请修改脚本中的PYTHON_BIN变量"
    exit 1
fi

# 检查脚本
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}❌ 分析脚本未找到: $SCRIPT_PATH${NC}"
    exit 1
fi

# 创建日志目录
mkdir -p "$LOG_DIR"

echo ""
echo -e "${GREEN}✅ 环境检查通过${NC}"
echo ""

# 生成crontab条目
CRON_JOB="0 15 * * * cd ${PROJECT_ROOT} && ${PYTHON_BIN} ${SCRIPT_PATH} --email >> ${LOG_DIR}/asset_analysis.log 2>&1"

echo "将要添加的定时任务:"
echo -e "${YELLOW}$CRON_JOB${NC}"
echo ""
echo "⏰ 执行时间: 每天下午3点 (15:00)"
echo "📧 邮件接收: 1264947688@qq.com"
echo "📝 日志文件: ${LOG_DIR}/asset_analysis.log"
echo ""

# 询问用户
read -p "是否继续安装? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消安装"
    exit 0
fi

# 检查crontab是否已存在
if crontab -l 2>/dev/null | grep -q "run_asset_analysis.py"; then
    echo -e "${YELLOW}⚠️  检测到已存在的定时任务${NC}"
    read -p "是否覆盖? (y/n): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "已取消安装"
        exit 0
    fi
    # 移除旧任务
    crontab -l 2>/dev/null | grep -v "run_asset_analysis.py" | crontab -
fi

# 添加新任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✅ 定时任务安装成功!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo "📌 下次执行时间:"
    echo "   每天下午3点 (15:00)"
    echo ""
    echo "📋 查看当前定时任务:"
    echo "   crontab -l"
    echo ""
    echo "📝 查看执行日志:"
    echo "   tail -f ${LOG_DIR}/asset_analysis.log"
    echo ""
    echo "🧪 测试邮件发送:"
    echo "   cd ${PROJECT_ROOT}"
    echo "   python3 ${SCRIPT_PATH} --email"
    echo ""
    echo "❌ 删除定时任务:"
    echo "   crontab -e  (手动删除包含 run_asset_analysis.py 的行)"
    echo ""
else
    echo -e "${RED}❌ 定时任务安装失败${NC}"
    exit 1
fi
