# -*- coding: utf-8 -*-
"""checker.py 的续篇：自检清单、风险汇总、总装与报告输出。

拆成两个文件只是为了单文件不过长，导入时 checker.py 会把这里的函数合并进来。
"""

from typing import Dict, Any, List

try:
    from rules import (
        REG_NAME, REG_EFFECTIVE, FORBIDDEN_ITEMS, RISK_TROPES, LANGUAGE_RULES,
        LABEL_RULES, AI_LABEL_RULE, AI_LABEL_DETAIL, PROMO_RULE, PENALTIES,
        ENFORCEMENT_FACTS, VOLUNTARY_UPGRADE, THRESHOLD_NOTE,
    )
except ImportError:
    from .rules import (  # type: ignore
        REG_NAME, REG_EFFECTIVE, FORBIDDEN_ITEMS, RISK_TROPES, LANGUAGE_RULES,
        LABEL_RULES, AI_LABEL_RULE, AI_LABEL_DETAIL, PROMO_RULE, PENALTIES,
        ENFORCEMENT_FACTS, VOLUNTARY_UPGRADE, THRESHOLD_NOTE,
    )

CATEGORY_NAME = {0: "不适用本办法（非微短剧）", 1: "一类微短剧", 2: "二类微短剧", 3: "三类微短剧"}
CATEGORY_GATE = {
    0: "—（本项目不适用本办法，无备案、审核、许可证、节目编号要求）",
    1: "《微短剧发行许可证》（省级以上广电主管部门颁发，总局统一印制）",
    2: "省级广电主管部门批准文件（编号规则由总局统一制定）",
    3: "播出单位播前审核并标注节目编号（同步线上报广电主管部门）",
}


# ---------------------------------------------------------------------------
# 6. 内容红线自检
# ---------------------------------------------------------------------------

def build_content_checklist(c: Dict[str, Any]) -> Dict[str, Any]:
    """生成可逐条勾选的红线自检表，并按项目题材点出高频踩雷情节。"""
    rows = []
    for idx, text in FORBIDDEN_ITEMS:
        rows.append([idx, text, "□ 已核 / □ 存疑"])

    subj = (" ".join(list(c.get("subjects") or [])) + " " +
            str(c.get("subject_desc") or "") + " " + str(c.get("title") or ""))

    hit_tropes = []
    for trope, item, why in RISK_TROPES:
        keywords = _trope_keywords(trope)
        if any(k in subj for k in keywords):
            hit_tropes.append((trope, item, why))

    return {"rows": rows, "tropes": RISK_TROPES, "hit_tropes": hit_tropes}


def _trope_keywords(trope: str) -> List[str]:
    """从踩雷情节描述里抽几个能和用户题材文本对上的词。"""
    table = {
        "重生复仇": ["重生", "复仇", "复仇者"],
        "霸总": ["霸总", "总裁", "豪门"],
        "赘婿": ["赘婿", "逆袭", "战神"],
        "未成年": ["校园", "学生", "高中", "未成年"],
        "神婆": ["玄学", "算命", "转运", "因果", "风水"],
        "民国": ["民国", "抗战", "谍战", "历史"],
        "擦边": ["擦边", "情色", "诱惑"],
        "公检法": ["刑侦", "警察", "律师", "检察", "缉毒", "扫黑"],
        "真实企业": ["影射", "原型"],
        "赌博": ["赌", "放贷", "荐股", "炒股", "期货"],
    }
    for key, words in table.items():
        if key in trope:
            return words
    return []


# ---------------------------------------------------------------------------
# 7. 标注与 AI 自检
# ---------------------------------------------------------------------------

def build_label_checklist(c: Dict[str, Any], category: int) -> Dict[str, Any]:
    items = list(LABEL_RULES)
    items[0] = ("片头明显位置标注剧名，以及本剧对应的%s"
                % ("许可证号" if category == 1 else
                   "批准文件编号" if category == 2 else "节目编号"))

    ai_block = None
    if c.get("uses_ai"):
        ai_block = {
            "rule": AI_LABEL_RULE,
            "detail": list(AI_LABEL_DETAIL),
            "scope": c.get("ai_scope") or "（未填写具体使用环节）",
        }

    return {"items": items, "language": list(LANGUAGE_RULES),
            "promo": PROMO_RULE, "ai": ai_block}


# ---------------------------------------------------------------------------
# 8. 风险与后果
# ---------------------------------------------------------------------------

def build_risks(category: int, qual: Dict[str, Any],
                applic: Dict[str, Any]) -> List[Dict[str, str]]:
    risks: List[Dict[str, str]] = []

    if not applic.get("applies"):
        risks.append({"等级": "需先厘清", "风险点": "适用性存疑",
                      "后果": "若不属于本办法所称微短剧，则应按对应的网络剧片或网络视听内容规定管理，"
                              "适用流程完全不同，按错赛道准备等于白做"})
        risks.append({"等级": "中", "风险点": "按错赛道准备合规材料",
                      "后果": "第二十五条的 11 条内容红线对所有网络视听内容普遍适用，本表仍可供内容自查；"
                              "但许可证／节目编号等要求不适用，请按网络剧（网络剧片）规定另行办理。"})
        return risks

    if qual.get("blocking"):
        risks.append({"等级": "阻断", "风险点": "申报主体不具备资质",
                      "后果": "备案公示无法受理，后续报审、发证全部无从谈起；"
                              "硬拍出来也拿不到许可，属于未取得许可擅自播出"})

    risks.append({"等级": "高", "风险点": "未取得许可证／批准文件／节目编号即上线",
                  "后果": "第十七条：不得播出，不得参加评奖评优；"
                          "第四十四条：擅自播出的依《广播电视管理条例》第五十条处罚"})

    risks.append({"等级": "高", "风险点": "内容触碰第二十五条红线",
                  "后果": "责令改正，可要求暂停节目内容更新；情节严重的依条例处罚。"
                          "推广物料（切片、封面、投流素材）同样受约束"})

    if category == 1:
        risks.append({"等级": "中", "风险点": "拍摄中擅自变更主要人物定位或故事整体走向",
                      "后果": "第十六条要求重新履行备案手续，等于流程重走一遍，工期直接失控"})
        risks.append({"等级": "中", "风险点": "被不予许可后转投其他省广电送审",
                      "后果": "第二十一条明令禁止转移送审，此路不通"})

    if category == 3:
        risks.append({"等级": "中", "风险点": "多平台分发时共用他方节目编号",
                      "后果": "第三十三条第（二）项：非独播的三类剧，各播出单位须按各自审核版本"
                              "标注本单位编号，共用编号属违规"})
        risks.append({"等级": "低", "风险点": "重播未重新审核",
                      "后果": "第三十五条要求重新播出的三类剧须按办法标准重新审核"})

    return risks


# ---------------------------------------------------------------------------
# 总装
# ---------------------------------------------------------------------------

def assemble(c, applic, cls, qual, steps, timeline, content, labels, risks):
    category = cls["category"]
    return {
        "case": c,
        "applicability": applic,
        "classification": cls,
        "category": category,
        "category_name": CATEGORY_NAME[category],
        "gate": CATEGORY_GATE[category],
        "qualification": qual,
        "workflow": steps,
        "timeline": timeline,
        "content": content,
        "labels": labels,
        "risks": risks,
        "upgrade_note": VOLUNTARY_UPGRADE if category == 3 else "",
        "enforcement": list(ENFORCEMENT_FACTS),
        "penalties": list(PENALTIES),
        "threshold_note": THRESHOLD_NOTE,
        "reg_name": REG_NAME,
        "reg_effective": REG_EFFECTIVE,
    }
