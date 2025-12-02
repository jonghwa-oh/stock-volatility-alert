#!/usr/bin/env python3
"""
로깅 유틸리티
모든 로그에 타임스탬프를 자동으로 추가합니다.
"""
from datetime import datetime
from typing import Optional


def log(message: str, prefix: Optional[str] = None):
    """
    타임스탬프와 함께 로그 출력
    
    Args:
        message: 로그 메시지
        prefix: 선택적 프리픽스 (예: "✅", "❌", "📊")
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if prefix:
        print(f"[{timestamp}] {prefix} {message}")
    else:
        print(f"[{timestamp}] {message}")


def log_section(title: str, width: int = 70):
    """
    섹션 제목 로그 (구분선 포함)
    
    Args:
        title: 섹션 제목
        width: 구분선 너비
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print()
    print("=" * width)
    print(f"[{timestamp}] {title}")
    print("=" * width)


def log_subsection(title: str, width: int = 40):
    """
    하위 섹션 제목 로그
    
    Args:
        title: 섹션 제목
        width: 구분선 너비
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print()
    print(f"[{timestamp}] {'-' * width}")
    print(f"[{timestamp}] {title}")
    print(f"[{timestamp}] {'-' * width}")


def log_success(message: str):
    """성공 로그"""
    log(message, "✅")


def log_error(message: str):
    """오류 로그"""
    log(message, "❌")


def log_warning(message: str):
    """경고 로그"""
    log(message, "⚠️")


def log_info(message: str):
    """정보 로그"""
    log(message, "ℹ️")


def log_debug(message: str):
    """디버그 로그"""
    log(message, "🔍")

