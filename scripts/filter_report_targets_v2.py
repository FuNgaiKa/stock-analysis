#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简市场洞察报告 - 只保留看多/强烈看多/中性偏多标的的详细分析 (V2完整版)

过滤策略:
1. 删除 "### 恒生科技" subsection (在"四大科技指数"内)
2. 删除11个 "## INDUSTRY: 标的名称" sections
"""
import re
from pathlib import Path

# 需要保留的14个标的
KEEP_TARGETS = {
    # 强烈看多 (5个)
    "纳斯达克", "港股创新药", "A股科创芯片", "三花智控", "指南针",
    # 看多 (3个)
    "黄金", "创业板指", "A股稀土",
    # 中性偏多 (6个)
    "比特币", "科创50", "沪深300", "A股钢铁", "A股软件", "阿里巴巴"
}

# 需要删除的11个标的
DELETE_TARGETS = {
    # 中性 (5个)
    "恒生科技", "A股煤炭", "A股化工", "A股电力", "A股白酒",
    # 看空 (6个)
    "港股电池", "A股证券", "A股银行", "A股保险", "A股有色金属", "A股半导体"
}


def should_keep_target(target_name: str) -> bool:
    """判断标的是否应该保留"""
    # 检查是否在保留列表中
    for keep in KEEP_TARGETS:
        if keep in target_name:
            return True
    # 检查是否在删除列表中
    for delete in DELETE_TARGETS:
        if delete in target_name:
            return False
    # 未知标的,默认保留
    return True


def filter_report(input_file: Path, output_file: Path):
    """
    过滤报告,删除不需要的标的详细分析

    处理两种格式:
    1. ### 标的名称 (在"四大科技指数"等分组章节内)
    2. ## INDUSTRY: 标的名称 (独立的行业章节)
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    i = 0
    deleted_count = 0
    kept_count = 0

    # State machine
    in_target_section = False
    target_section_buffer = []
    current_target_name = None
    section_level = None  # "###" or "##"

    while i < len(lines):
        line = lines[i]

        # 检测目标章节的开始
        # Pattern 1: ### 标的名称 (不含####的子章节)
        if re.match(r'^### [^#]', line) and not re.match(r'^#### ', line):
            # 先处理之前积累的章节
            if in_target_section and target_section_buffer:
                if should_keep_target(current_target_name):
                    result_lines.extend(target_section_buffer)
                    kept_count += 1
                    print(f"  ✅ 保留: {current_target_name}")
                else:
                    deleted_count += 1
                    print(f"  🗑️  删除: {current_target_name}")
                target_section_buffer = []

            # 开始新的目标章节
            target_name = line.replace("###", "").strip()
            current_target_name = target_name
            section_level = "###"
            in_target_section = True
            target_section_buffer = [line]
            i += 1
            continue

        # Pattern 2: ## INDUSTRY: 标的名称
        if re.match(r'^## [A-Z]+: ', line):
            # 先处理之前积累的章节
            if in_target_section and target_section_buffer:
                if should_keep_target(current_target_name):
                    result_lines.extend(target_section_buffer)
                    kept_count += 1
                    print(f"  ✅ 保留: {current_target_name}")
                else:
                    deleted_count += 1
                    print(f"  🗑️  删除: {current_target_name}")
                target_section_buffer = []

            # 开始新的目标章节
            match = re.match(r'^## [A-Z]+: (.+)$', line)
            if match:
                target_name = match.group(1).strip()
                current_target_name = target_name
                section_level = "##"
                in_target_section = True
                target_section_buffer = [line]
                i += 1
                continue

        # 检测章节结束
        # 如果遇到同级或更高级的章节标题,说明当前章节结束
        if in_target_section:
            if section_level == "###":
                # ### 章节遇到 ###, ##, # 就结束
                if line.startswith("###") and not line.startswith("####"):
                    # 这是新的同级章节,先保存当前章节
                    if should_keep_target(current_target_name):
                        result_lines.extend(target_section_buffer)
                        kept_count += 1
                        print(f"  ✅ 保留: {current_target_name}")
                    else:
                        deleted_count += 1
                        print(f"  🗑️  删除: {current_target_name}")

                    # 重新处理这一行 (新章节的开始)
                    target_section_buffer = []
                    in_target_section = False
                    continue

                elif line.startswith("##") and not line.startswith("###"):
                    # 遇到更高级章节,结束当前章节
                    if should_keep_target(current_target_name):
                        result_lines.extend(target_section_buffer)
                        kept_count += 1
                        print(f"  ✅ 保留: {current_target_name}")
                    else:
                        deleted_count += 1
                        print(f"  🗑️  删除: {current_target_name}")

                    target_section_buffer = []
                    in_target_section = False
                    # 这一行不是目标章节,直接保留
                    result_lines.append(line)
                    i += 1
                    continue

                else:
                    # 还在当前章节内,继续积累
                    target_section_buffer.append(line)
                    i += 1
                    continue

            elif section_level == "##":
                # ## 章节遇到 ##, # 就结束
                if line.startswith("##") and not re.match(r'^## [A-Z]+: ', line):
                    # 遇到非目标格式的 ## 章节,结束当前章节
                    if should_keep_target(current_target_name):
                        result_lines.extend(target_section_buffer)
                        kept_count += 1
                        print(f"  ✅ 保留: {current_target_name}")
                    else:
                        deleted_count += 1
                        print(f"  🗑️  删除: {current_target_name}")

                    target_section_buffer = []
                    in_target_section = False
                    # 这一行不是目标章节,直接保留
                    result_lines.append(line)
                    i += 1
                    continue

                elif re.match(r'^## [A-Z]+: ', line):
                    # 遇到新的行业章节,结束当前章节,重新处理这一行
                    if should_keep_target(current_target_name):
                        result_lines.extend(target_section_buffer)
                        kept_count += 1
                        print(f"  ✅ 保留: {current_target_name}")
                    else:
                        deleted_count += 1
                        print(f"  🗑️  删除: {current_target_name}")

                    target_section_buffer = []
                    in_target_section = False
                    continue

                else:
                    # 还在当前章节内,继续积累
                    target_section_buffer.append(line)
                    i += 1
                    continue

        # 不在目标章节内,直接保留
        result_lines.append(line)
        i += 1

    # 处理最后一个章节
    if in_target_section and target_section_buffer:
        if should_keep_target(current_target_name):
            result_lines.extend(target_section_buffer)
            kept_count += 1
            print(f"  ✅ 保留: {current_target_name}")
        else:
            deleted_count += 1
            print(f"  🗑️  删除: {current_target_name}")

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    # 统计信息
    original_lines = len(lines)
    filtered_lines = len(result_lines)
    saved_lines = original_lines - filtered_lines
    saved_pct = saved_lines / original_lines * 100 if original_lines > 0 else 0

    print(f"\n📊 统计信息:")
    print(f"  原始行数: {original_lines}")
    print(f"  精简后行数: {filtered_lines}")
    print(f"  减少行数: {saved_lines} ({saved_pct:.1f}%)")
    print(f"  保留标的: {kept_count}个")
    print(f"  删除标的: {deleted_count}个")


if __name__ == "__main__":
    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    # 先恢复原始报告
    original_file = project_root / "russ_trading" / "reports" / "daily" / "2025-11" / "市场洞察报告_20251114_原始.md"
    target_file = project_root / "russ_trading" / "reports" / "daily" / "2025-11" / "市场洞察报告_20251114.md"

    if original_file.exists():
        print("📋 从原始文件恢复...")
        import shutil
        shutil.copy(original_file, target_file)
        print(f"✅ 已从 {original_file.name} 恢复")
    else:
        print("⚠️ 未找到原始备份文件,使用当前文件")

    print("\n🚀 开始精简市场洞察报告...")
    print(f"📄 文件: {target_file}")
    print()

    if not target_file.exists():
        print(f"❌ 文件不存在: {target_file}")
        exit(1)

    filter_report(target_file, target_file)

    print("\n✅ 报告精简完成!")
    print("\n💡 提示:")
    print("  - 如需查看完整报告: 市场洞察报告_20251114_原始.md")
    print("  - 精简报告: 市场洞察报告_20251114.md")
