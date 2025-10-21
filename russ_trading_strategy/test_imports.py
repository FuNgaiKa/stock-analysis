#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple import test without emojis"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("Testing Module Imports")
print("=" * 80)

# Test 1: Config loader
print("\nTest 1: Config Loader")
try:
    from russ_trading_strategy.utils.config_loader import get_risk_profile
    config = get_risk_profile('aggressive')
    print(f"   PASS - Loaded risk profile")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

# Test 2: Logger
print("\nTest 2: Logger")
try:
    from russ_trading_strategy.utils.logger import setup_logger
    logger = setup_logger('test', log_to_file=False)
    print("   PASS")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

# Test 3: Cache
print("\nTest 3: Cache Manager")
try:
    from russ_trading_strategy.utils.cache_manager import SimpleCache
    cache = SimpleCache()
    print("   PASS")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

# Test 4: Core modules
print("\nTest 4: Core Modules")
try:
    from russ_trading_strategy.core import (
        QuantAnalyzer,
        StressTester,
        ScenarioAnalyzer,
        AttributionAnalyzer,
        ExecutiveSummaryGenerator,
        ChartGenerator
    )
    print("   PASS - All 6 core modules imported")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

# Test 5: Original modules
print("\nTest 5: Original Modules")
try:
    from russ_trading_strategy.position_health_checker import PositionHealthChecker
    from russ_trading_strategy.performance_tracker import PerformanceTracker
    from russ_trading_strategy.daily_position_report_generator import DailyPositionReportGenerator
    print("   PASS")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

# Test 6: Enhanced report generator v2
print("\nTest 6: Enhanced Report Generator v2")
try:
    from russ_trading_strategy.daily_position_report_generator_v2 import EnhancedReportGenerator
    generator = EnhancedReportGenerator()
    print("   PASS")
except Exception as e:
    print(f"   FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("All imports successful!")
print("=" * 80)
