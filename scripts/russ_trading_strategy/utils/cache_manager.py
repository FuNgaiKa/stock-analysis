#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器
Cache Manager

提供数据缓存功能,减少重复计算和数据获取
支持内存缓存和可选的Redis缓存
"""

import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
from functools import wraps
import hashlib


class SimpleCache:
    """简单内存缓存 (不依赖Redis)"""

    def __init__(self, cache_dir: Path = None):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录,如果为None则使用项目cache目录
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent.parent / 'cache'
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        # 内存缓存
        self._memory_cache = {}

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用MD5避免文件名过长
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键
            use_memory: 是否使用内存缓存

        Returns:
            缓存值,如果不存在或已过期则返回None
        """
        # 先查内存缓存
        if use_memory and key in self._memory_cache:
            data, expire_time = self._memory_cache[key]
            if expire_time is None or datetime.now() < expire_time:
                return data
            else:
                # 过期则删除
                del self._memory_cache[key]

        # 查文件缓存
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)

                expire_time = cached_data.get('expire_time')
                if expire_time is None or datetime.now() < expire_time:
                    data = cached_data['data']
                    # 回填内存缓存
                    if use_memory:
                        self._memory_cache[key] = (data, expire_time)
                    return data
                else:
                    # 过期删除
                    cache_path.unlink()
            except Exception:
                # 缓存损坏,删除
                cache_path.unlink()

        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 86400,
        use_memory: bool = True
    ) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒),None表示永不过期
            use_memory: 是否同时缓存到内存
        """
        expire_time = None if ttl is None else datetime.now() + timedelta(seconds=ttl)

        # 内存缓存
        if use_memory:
            self._memory_cache[key] = (value, expire_time)

        # 文件缓存
        cache_path = self._get_cache_path(key)
        cached_data = {
            'data': value,
            'expire_time': expire_time,
            'created_at': datetime.now()
        }

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception as e:
            # 缓存失败不影响主流程
            print(f"Warning: Failed to cache data: {e}")

    def delete(self, key: str) -> None:
        """删除缓存"""
        # 删除内存缓存
        if key in self._memory_cache:
            del self._memory_cache[key]

        # 删除文件缓存
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()

    def clear(self) -> None:
        """清空所有缓存"""
        # 清空内存
        self._memory_cache.clear()

        # 清空文件
        for cache_file in self.cache_dir.glob('*.cache'):
            cache_file.unlink()

    def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的缓存数量
        """
        cleaned = 0

        # 清理内存缓存
        expired_keys = []
        for key, (data, expire_time) in self._memory_cache.items():
            if expire_time and datetime.now() >= expire_time:
                expired_keys.append(key)

        for key in expired_keys:
            del self._memory_cache[key]
            cleaned += 1

        # 清理文件缓存
        for cache_file in self.cache_dir.glob('*.cache'):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)

                expire_time = cached_data.get('expire_time')
                if expire_time and datetime.now() >= expire_time:
                    cache_file.unlink()
                    cleaned += 1
            except Exception:
                # 损坏的缓存文件也删除
                cache_file.unlink()
                cleaned += 1

        return cleaned


# 全局缓存实例
_cache = SimpleCache()


def cached(
    key_prefix: str = '',
    ttl: int = 86400,
    use_args: bool = True
):
    """
    缓存装饰器

    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间(秒)
        use_args: 是否将函数参数加入缓存键

    Usage:
        @cached(key_prefix='market_data', ttl=3600)
        def fetch_market_data(date):
            # ... 耗时操作
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if use_args:
                # 将参数转换为字符串
                args_str = '_'.join(str(arg) for arg in args)
                kwargs_str = '_'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"
            else:
                cache_key = f"{key_prefix}:{func.__name__}"

            # 尝试从缓存获取
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            _cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def cache_market_data(date: str):
    """便捷函数:缓存市场数据(当日有效)"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"market_data:{date}"

            # 检查缓存
            cached = _cache.get(cache_key)
            if cached:
                return cached

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存到当日23:59
            now = datetime.now()
            expire_at = now.replace(hour=23, minute=59, second=59)
            ttl = int((expire_at - now).total_seconds())

            _cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


if __name__ == '__main__':
    # 测试缓存系统
    import time

    print("=== 测试基本缓存功能 ===")
    cache = SimpleCache()

    # 设置缓存
    cache.set('test_key', {'data': 'test_value'}, ttl=5)

    # 获取缓存
    value = cache.get('test_key')
    print(f"缓存值: {value}")

    # 等待过期
    print("等待5秒让缓存过期...")
    time.sleep(6)

    value = cache.get('test_key')
    print(f"过期后的缓存值: {value}")

    print("\n=== 测试缓存装饰器 ===")

    @cached(key_prefix='test', ttl=3600)
    def expensive_calculation(x, y):
        print(f"执行计算: {x} + {y}")
        time.sleep(1)  # 模拟耗时操作
        return x + y

    # 第一次调用 - 会执行计算
    start = time.time()
    result1 = expensive_calculation(10, 20)
    print(f"第一次调用结果: {result1}, 耗时: {time.time()-start:.2f}秒")

    # 第二次调用 - 从缓存获取
    start = time.time()
    result2 = expensive_calculation(10, 20)
    print(f"第二次调用结果: {result2}, 耗时: {time.time()-start:.2f}秒")

    print("\n=== 测试缓存清理 ===")
    cleaned = cache.cleanup_expired()
    print(f"清理了{cleaned}个过期缓存")
