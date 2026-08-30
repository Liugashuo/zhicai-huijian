# -*- coding: utf-8 -*-
"""SITES 配置化：新增电商平台只需实现 extract_details 钩子，无需改动 Agent 主循环。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SiteConfig:
    key: str
    name: str
    base_url: str
    categories: list[str] = field(default_factory=list)
    extract_hook: str | None = None


SITES: dict[str, SiteConfig] = {
    "jd": SiteConfig("jd", "京东", "https://www.jd.com", categories=["电子", "办公"]),
    "taobao": SiteConfig("taobao", "淘宝", "https://www.taobao.com", categories=["电子", "通用物资"]),
    "pdd": SiteConfig("pdd", "拼多多", "https://www.pinduoduo.com", categories=["通用物资"]),
    "1688": SiteConfig("1688", "1688", "https://www.1688.com", categories=["电子", "办公", "通用物资"]),
    "industry_portal": SiteConfig("industry_portal", "行业门户", "", categories=["工程服务"]),
}


def sites_for_category(category: str) -> list[SiteConfig]:
    return [s for s in SITES.values() if category in s.categories]
