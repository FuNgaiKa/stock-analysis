#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器
Configuration Loader

负责加载YAML配置文件并提供全局访问
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from functools import lru_cache


class ConfigLoader:
    """配置加载器"""

    def __init__(self):
        """初始化配置加载器"""
        self.config_dir = Path(__file__).parent.parent / 'config'
        self._risk_profiles = None
        self._market_config = None

    @lru_cache(maxsize=1)
    def load_risk_profiles(self) -> Dict[str, Any]:
        """
        加载风险配置文件

        Returns:
            风险配置字典
        """
        if self._risk_profiles is None:
            config_path = self.config_dir / 'risk_profiles.yaml'
            with open(config_path, 'r', encoding='utf-8') as f:
                self._risk_profiles = yaml.safe_load(f)
        return self._risk_profiles

    @lru_cache(maxsize=1)
    def load_market_config(self) -> Dict[str, Any]:
        """
        加载市场配置文件

        Returns:
            市场配置字典
        """
        if self._market_config is None:
            config_path = self.config_dir / 'market_config.yaml'
            with open(config_path, 'r', encoding='utf-8') as f:
                self._market_config = yaml.safe_load(f)
        return self._market_config

    def get_risk_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        获取指定风险配置

        Args:
            profile_name: 风险配置名称 (conservative/moderate/aggressive/ultra_aggressive)

        Returns:
            风险配置字典
        """
        profiles = self.load_risk_profiles()
        if profile_name not in profiles:
            raise ValueError(
                f"Unknown risk profile: {profile_name}. "
                f"Available: {list(profiles.keys())}"
            )
        return profiles[profile_name]

    def get_benchmarks(self) -> Dict[str, float]:
        """获取基准点位"""
        config = self.load_market_config()
        return config.get('benchmarks', {})

    def get_historical_crises(self) -> list:
        """获取历史危机数据"""
        config = self.load_market_config()
        return config.get('historical_crises', [])

    def get_scenario_config(self) -> Dict[str, Any]:
        """获取情景分析配置"""
        config = self.load_market_config()
        return config.get('scenario_analysis', {})

    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        config = self.load_market_config()
        return config.get('cache', {})


# 全局单例
_config_loader = ConfigLoader()


def get_risk_profile(profile_name: str) -> Dict[str, Any]:
    """便捷函数:获取风险配置"""
    return _config_loader.get_risk_profile(profile_name)


def get_benchmarks() -> Dict[str, float]:
    """便捷函数:获取基准点位"""
    return _config_loader.get_benchmarks()


def get_historical_crises() -> list:
    """便捷函数:获取历史危机数据"""
    return _config_loader.get_historical_crises()


def get_scenario_config() -> Dict[str, Any]:
    """便捷函数:获取情景分析配置"""
    return _config_loader.get_scenario_config()


def get_cache_config() -> Dict[str, Any]:
    """便捷函数:获取缓存配置"""
    return _config_loader.get_cache_config()


if __name__ == '__main__':
    # 测试配置加载
    print("=== 测试风险配置加载 ===")
    aggressive = get_risk_profile('aggressive')
    print(f"积极型配置: {aggressive['name']}")
    print(f"目标年化: {aggressive['target_annual_return']*100}%")

    print("\n=== 测试基准点位加载 ===")
    benchmarks = get_benchmarks()
    print(f"沪深300基准: {benchmarks['hs300']}")

    print("\n=== 测试历史危机数据 ===")
    crises = get_historical_crises()
    print(f"共有{len(crises)}个历史危机数据")
    for crisis in crises:
        print(f"- {crisis['name']}: {crisis['market_drop']*100}%")
