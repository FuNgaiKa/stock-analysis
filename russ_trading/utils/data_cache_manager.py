#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据缓存管理器
Data Cache Manager

实现三级缓存机制:
1. 内存缓存 - 单次运行内复用
2. 文件缓存 - 跨运行复用(当日有效)
3. 智能缓存失效 - 自动清理过期数据

作者: Claude Code
日期: 2025-11-14
"""

import os
import pickle
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Callable, Dict
import pandas as pd

logger = logging.getLogger(__name__)


class DataCacheManager:
    """
    数据缓存管理器

    特性:
    - 内存缓存: 进程内数据复用
    - 文件缓存: 持久化缓存,跨运行复用
    - 自动过期: 根据数据类型设置不同TTL
    - 线程安全: 支持并发访问
    """

    def __init__(self, cache_dir: Optional[Path] = None, enable_file_cache: bool = True):
        """
        初始化缓存管理器

        Args:
            cache_dir: 文件缓存目录,默认为项目根目录/data/cache
            enable_file_cache: 是否启用文件缓存
        """
        # 内存缓存
        self._memory_cache: Dict[str, tuple] = {}  # {key: (data, timestamp)}

        # 文件缓存配置
        self.enable_file_cache = enable_file_cache
        if cache_dir is None:
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / "data" / "cache"

        self.cache_dir = Path(cache_dir)
        if self.enable_file_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"文件缓存目录: {self.cache_dir}")

        # 默认TTL配置(秒)
        self.default_ttls = {
            'intraday': 300,        # 5分钟 - 盘中数据
            'daily': 86400,         # 24小时 - 日线数据
            'historical': 604800,   # 7天 - 历史数据
            'static': 2592000,      # 30天 - 静态配置
        }

    def get_or_fetch(
        self,
        key: str,
        fetcher: Callable,
        ttl: Optional[int] = None,
        cache_type: str = 'daily',
        force_refresh: bool = False
    ) -> Any:
        """
        获取缓存数据或调用fetcher获取新数据

        Args:
            key: 缓存键
            fetcher: 数据获取函数
            ttl: 缓存有效期(秒),None表示使用默认值
            cache_type: 缓存类型 (intraday/daily/historical/static)
            force_refresh: 强制刷新,忽略缓存

        Returns:
            数据对象
        """
        if force_refresh:
            data = fetcher()
            self._set_cache(key, data, ttl or self.default_ttls.get(cache_type, 86400))
            return data

        # 1. 尝试内存缓存
        cached_data = self._get_memory_cache(key, ttl or self.default_ttls.get(cache_type, 86400))
        if cached_data is not None:
            logger.debug(f"内存缓存命中: {key}")
            return cached_data

        # 2. 尝试文件缓存
        if self.enable_file_cache:
            cached_data = self._get_file_cache(key, ttl or self.default_ttls.get(cache_type, 86400))
            if cached_data is not None:
                logger.debug(f"文件缓存命中: {key}")
                # 回写到内存缓存
                self._memory_cache[key] = (cached_data, datetime.now())
                return cached_data

        # 3. 缓存未命中,获取新数据
        logger.debug(f"缓存未命中,获取数据: {key}")
        try:
            data = fetcher()
            # 保存到缓存
            self._set_cache(key, data, ttl or self.default_ttls.get(cache_type, 86400))
            return data
        except Exception as e:
            logger.error(f"获取数据失败 {key}: {e}")
            raise

    def _get_memory_cache(self, key: str, ttl: int) -> Optional[Any]:
        """从内存缓存获取数据"""
        if key not in self._memory_cache:
            return None

        data, timestamp = self._memory_cache[key]

        # 检查是否过期
        if (datetime.now() - timestamp).total_seconds() > ttl:
            del self._memory_cache[key]
            return None

        return data

    def _get_file_cache(self, key: str, ttl: int) -> Optional[Any]:
        """从文件缓存获取数据"""
        cache_file = self._get_cache_file_path(key)

        if not cache_file.exists():
            return None

        # 检查文件修改时间
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if (datetime.now() - mtime).total_seconds() > ttl:
            # 过期,删除
            cache_file.unlink()
            return None

        # 读取缓存
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            logger.warning(f"读取文件缓存失败 {key}: {e}")
            cache_file.unlink()
            return None

    def _set_cache(self, key: str, data: Any, ttl: int):
        """保存数据到缓存"""
        # 1. 保存到内存
        self._memory_cache[key] = (data, datetime.now())

        # 2. 保存到文件
        if self.enable_file_cache:
            try:
                cache_file = self._get_cache_file_path(key)
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
                logger.debug(f"数据已缓存: {key}")
            except Exception as e:
                logger.warning(f"保存文件缓存失败 {key}: {e}")

    def _get_cache_file_path(self, key: str) -> Path:
        """生成缓存文件路径"""
        # 使用日期作为子目录,便于清理
        today = datetime.now().strftime('%Y%m%d')
        cache_subdir = self.cache_dir / today
        cache_subdir.mkdir(parents=True, exist_ok=True)

        # 使用MD5哈希作为文件名(避免特殊字符)
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return cache_subdir / f"{hash_key}.pkl"

    def clear_memory_cache(self):
        """清空内存缓存"""
        self._memory_cache.clear()
        logger.info("内存缓存已清空")

    def clear_file_cache(self, days_to_keep: int = 1):
        """
        清理过期文件缓存

        Args:
            days_to_keep: 保留最近N天的缓存
        """
        if not self.enable_file_cache:
            return

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        deleted_count = 0
        for date_dir in self.cache_dir.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                dir_date = datetime.strptime(date_dir.name, '%Y%m%d')
                if dir_date < cutoff_date:
                    # 删除整个目录
                    for cache_file in date_dir.glob('*.pkl'):
                        cache_file.unlink()
                        deleted_count += 1
                    date_dir.rmdir()
            except ValueError:
                # 忽略非日期格式的目录
                pass

        logger.info(f"清理过期文件缓存: 删除 {deleted_count} 个文件")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            'memory_cache_size': len(self._memory_cache),
            'memory_cache_keys': list(self._memory_cache.keys())
        }

        if self.enable_file_cache and self.cache_dir.exists():
            total_files = 0
            total_size = 0
            for cache_file in self.cache_dir.rglob('*.pkl'):
                total_files += 1
                total_size += cache_file.stat().st_size

            stats['file_cache_count'] = total_files
            stats['file_cache_size_mb'] = round(total_size / 1024 / 1024, 2)

        return stats


# 全局单例实例
_global_cache_manager: Optional[DataCacheManager] = None


def get_cache_manager(
    cache_dir: Optional[Path] = None,
    enable_file_cache: bool = True
) -> DataCacheManager:
    """
    获取全局缓存管理器单例

    Args:
        cache_dir: 缓存目录
        enable_file_cache: 是否启用文件缓存

    Returns:
        DataCacheManager实例
    """
    global _global_cache_manager

    if _global_cache_manager is None:
        _global_cache_manager = DataCacheManager(
            cache_dir=cache_dir,
            enable_file_cache=enable_file_cache
        )

    return _global_cache_manager


if __name__ == '__main__':
    """测试代码"""
    import time

    # 初始化缓存管理器
    cache = get_cache_manager()

    print("=" * 80)
    print("数据缓存管理器测试")
    print("=" * 80)

    # 测试1: 基本缓存功能
    print("\n测试1: 基本缓存功能")

    def slow_fetcher():
        print("  执行耗时操作...")
        time.sleep(1)
        return {"data": "test_value", "timestamp": datetime.now().isoformat()}

    print("第一次获取(应该调用fetcher):")
    start = time.time()
    result1 = cache.get_or_fetch('test_key_1', slow_fetcher, cache_type='daily')
    print(f"  耗时: {time.time() - start:.2f}秒")
    print(f"  结果: {result1}")

    print("\n第二次获取(应该使用内存缓存):")
    start = time.time()
    result2 = cache.get_or_fetch('test_key_1', slow_fetcher, cache_type='daily')
    print(f"  耗时: {time.time() - start:.2f}秒")
    print(f"  结果: {result2}")

    # 测试2: 缓存统计
    print("\n测试2: 缓存统计")
    stats = cache.get_cache_stats()
    print(f"  内存缓存数量: {stats['memory_cache_size']}")
    print(f"  文件缓存数量: {stats.get('file_cache_count', 0)}")
    print(f"  文件缓存大小: {stats.get('file_cache_size_mb', 0)} MB")

    # 测试3: DataFrame缓存
    print("\n测试3: DataFrame缓存")

    def fetch_dataframe():
        print("  生成DataFrame...")
        return pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=100),
            'value': range(100)
        })

    start = time.time()
    df1 = cache.get_or_fetch('test_df', fetch_dataframe, cache_type='historical')
    print(f"  第一次获取耗时: {time.time() - start:.2f}秒, shape: {df1.shape}")

    start = time.time()
    df2 = cache.get_or_fetch('test_df', fetch_dataframe, cache_type='historical')
    print(f"  第二次获取耗时: {time.time() - start:.2f}秒, shape: {df2.shape}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
