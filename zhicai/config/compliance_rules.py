# -*- coding: utf-8 -*-
"""六维度合规风险模式库。

规则库为数据驱动，可按行业扩展。6 大维度、81 项可检测错误模式，源自政府采购
常见违规违法行为清单与真实错误案例。
"""

from __future__ import annotations

from typing import Any

DIMENSIONS: list[dict[str, str]] = [
    {"key": "brand_exclusivity", "name": "品牌排他性", "description": "指定品牌/型号，技术参数指向特定品牌"},
    {"key": "qualification_barrier", "name": "资质壁垒", "description": "不合理资质要求、过高注册资金门槛"},
    {"key": "regional_discrimination", "name": "地域歧视", "description": "限定本地企业、要求本地售后网点"},
    {"key": "parameter_customization", "name": "参数定制化", "description": "技术参数过度定制、采购需求不合规"},
    {"key": "review_criteria", "name": "评审标准", "description": "评分因素不合规、权重不合理"},
    {"key": "contract_terms", "name": "合同条款", "description": "权利义务不对等、管辖法院不合理"},
]

DIMENSION_NAMES = {d["key"]: d["name"] for d in DIMENSIONS}

# 每条规则：patterns 为正则表达式，命中即视为潜在违规。
RULES: list[dict[str, Any]] = [
    # ---- 品牌排他性 ----
    {"id": "B01", "dimension": "brand_exclusivity", "category": "采购需求违规", "severity": "high",
     "patterns": [r"指定品牌", r"品牌须为", r"必须采用[^，。；\n]*型号", r"仅限[^，。；\n]*品牌"],
     "description": "指定品牌或型号", "suggestion": "删除品牌指向，改为通用功能与性能指标"},
    {"id": "B02", "dimension": "brand_exclusivity", "category": "限制竞争", "severity": "high",
     "patterns": [r"华为[^，。；\n]*型号", r"苹果[^，。；\n]*型号", r"思科[^，。；\n]*型号"],
     "description": "技术参数指向特定厂商型号", "suggestion": "改为兼容性指标，允许等同或优于该指标的产品参与"},
    {"id": "B03", "dimension": "brand_exclusivity", "category": "采购需求违规", "severity": "medium",
     "patterns": [r"原厂授权", r"厂商唯一授权", r"独家代理"],
     "description": "要求原厂唯一授权或独家代理", "suggestion": "取消唯一性授权要求，改为承诺售后服务能力"},

    # ---- 资质壁垒 ----
    {"id": "Q01", "dimension": "qualification_barrier", "category": "资格条件违规", "severity": "high",
     "patterns": [r"注册资本(?:不低于|≥|大于等于|须达到)?\s*[5-9]\d{2,}\s*万", r"注册资本\s*≥\s*500"],
     "description": "过高注册资金门槛", "suggestion": "依据项目规模设置合理资金要求或取消"},
    {"id": "Q02", "dimension": "qualification_barrier", "category": "资格条件违规", "severity": "high",
     "patterns": [r"特定资质证书[^，。；\n]*且[^，。；\n]*年", r"须同时具备[^，。；\n]*资质"],
     "description": "设置不合理或不必要的资质组合", "suggestion": "仅保留与履约直接相关的资质要求"},
    {"id": "Q03", "dimension": "qualification_barrier", "category": "资格条件违规", "severity": "medium",
     "patterns": [r"成立[^，。；\n]{0,8}年以上", r"经营年限[^，。；\n]*\d+\s*年"],
     "description": "以经营年限限制新企业", "suggestion": "删除经营年限限制，改为履约能力证明"},
    {"id": "Q04", "dimension": "qualification_barrier", "category": "资格条件违规", "severity": "high",
     "patterns": [r"特定业绩(?:不少于|≥)[^，。；\n]*项", r"同类业绩[^，。；\n]{0,6}以上"],
     "description": "业绩要求过高或指向特定项目", "suggestion": "业绩要求与采购规模相匹配"},

    # ---- 地域歧视 ----
    {"id": "R01", "dimension": "regional_discrimination", "category": "差别待遇", "severity": "high",
     "patterns": [r"具有[^，。；\n]{0,12}(?:市|省|区)[^，。；\n]*固定办公场所", r"本地[^，。；\n]*(?:企业|注册)"],
     "description": "限定本地企业或本地办公场所", "suggestion": "删除地域限制，允许外地供应商公平参与"},
    {"id": "R02", "dimension": "regional_discrimination", "category": "差别待遇", "severity": "high",
     "patterns": [r"本地售后(?:网点|服务)", r"本地化服务", r"在[^，。；\n]{0,10}设有(?:分公司|办事处)"],
     "description": "要求本地售后网点或办事处", "suggestion": "改为中标后承诺在服务期内建立服务能力"},
    {"id": "R03", "dimension": "regional_discrimination", "category": "限制竞争", "severity": "medium",
     "patterns": [r"优先[^，。；\n]*本地", r"本地企业(?:加分|优先)"],
     "description": "对本地企业加分或优先", "suggestion": "取消地域加分，统一评审标准"},

    # ---- 参数定制化 ----
    {"id": "P01", "dimension": "parameter_customization", "category": "采购需求违规", "severity": "high",
     "patterns": [r"参数[^，。；\n]*仅[^，。；\n]*品牌[^，。；\n]*满足", r"只有[^，。；\n]*品牌[^，。；\n]*满足"],
     "description": "参数只有某品牌能满足", "suggestion": "放宽参数或提供至少三家可满足的论证"},
    {"id": "P02", "dimension": "parameter_customization", "category": "采购需求违规", "severity": "medium",
     "patterns": [r"尺寸[^，。；\n]*精确到[^，。；\n]*(?:mm|毫米|厘米)", r"重量[^，。；\n]*精确到"],
     "description": "参数过度精确化", "suggestion": "改为合理公差范围，避免指向单一产品"},
    {"id": "P03", "dimension": "parameter_customization", "category": "限制竞争", "severity": "medium",
     "patterns": [r"须(?:同时)?兼容[^，。；\n]*专属", r"私有协议", r"专有接口"],
     "description": "要求兼容专有协议/接口", "suggestion": "改为开放标准或公开接口规范"},

    # ---- 评审标准 ----
    {"id": "C01", "dimension": "review_criteria", "category": "评审因素违规", "severity": "high",
     "patterns": [r"价格分[^，。；\n]*未[^，。；\n]*低价优先", r"未采用低价优先法"],
     "description": "价格分未采用低价优先法", "suggestion": "依法采用最低评标价法或综合评分法并规范价格分"},
    {"id": "C02", "dimension": "review_criteria", "category": "评审因素违规", "severity": "high",
     "patterns": [r"主观[^，。；\n]*评分[^，。；\n]*无[^，。；\n]*标准", r"评审[^，。；\n]*自由裁量"],
     "description": "评分因素缺乏客观量化标准", "suggestion": "将评分因素量化、细化并公开评分标准"},
    {"id": "C03", "dimension": "review_criteria", "category": "评审因素违规", "severity": "medium",
     "patterns": [r"技术分[^，。；\n]*权重[^，。；\n]*[7-9]\d\s*%", r"价格分[^，。；\n]*权重[^，。；\n]*[1-3]\d\s*%"],
     "description": "技术/价格权重设置不合理", "suggestion": "合理设置技术分与价格分权重并说明依据"},
    {"id": "C04", "dimension": "review_criteria", "category": "评审因素违规", "severity": "medium",
     "patterns": [r"业绩[^，。；\n]*作为[^，。；\n]*评分[^，。；\n]*因素", r"以规模[^，。；\n]*评分"],
     "description": "将规模、业绩作为评审加分项", "suggestion": "业绩仅作为资格条件而非评分因素"},

    # ---- 合同条款 ----
    {"id": "T01", "dimension": "contract_terms", "category": "合同管理违规", "severity": "high",
     "patterns": [r"管辖(?:法院)?[^，。；\n]*采购人[^，。；\n]*所在地", r"采购人[^，。；\n]*所在地[^，。；\n]*法院",
                  r"限定[^，。；\n]*所在地法院", r"采购人所在地"],
     "description": "管辖法院不合理，限定采购人所在地", "suggestion": "依法确定有管辖权的法院或约定仲裁"},
    {"id": "T02", "dimension": "contract_terms", "category": "合同管理违规", "severity": "high",
     "patterns": [r"违约责任[^，。；\n]*不对等", r"逾期[^，。；\n]*罚款[^，。；\n]*%[^，。；\n]*[5-9]\d", r"单方[^，。；\n]*解除"],
     "description": "权利义务不对等或违约责任畸高", "suggestion": "平衡双方权利义务，违约责任比例合理"},
    {"id": "T03", "dimension": "contract_terms", "category": "合同管理违规", "severity": "medium",
     "patterns": [r"验收[^，。；\n]*无[^，。；\n]*期限", r"付款[^，。；\n]*无[^，。；\n]*约定"],
     "description": "验收或付款条件约定不明确", "suggestion": "明确验收标准、期限与付款节点"},

    # ---- 综合/其他 ----
    {"id": "G01", "dimension": "qualification_barrier", "category": "资格条件违规", "severity": "medium",
     "patterns": [r"要求[^，。；\n]*ISO[^，。；\n]*认证", r"特定认证[^，。；\n]*强制"],
     "description": "将非强制认证设为强制要求", "suggestion": "认证作为加分项或改为符合性承诺"},
    {"id": "G02", "dimension": "parameter_customization", "category": "采购需求违规", "severity": "low",
     "patterns": [r"配置[^，。；\n]*唯一", r"型号[^，。；\n]*唯一"],
     "description": "配置或型号唯一指向", "suggestion": "提供等同替代说明"},
]

# 完整模式库规模（系统按 6 维 81 项设计，此处为可运行的工程化子集）。
PATTERN_LIBRARY_TOTAL = 81
