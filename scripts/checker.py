# -*- coding: utf-8 -*-
"""
微短剧合规自检与备案指引引擎
==============================
输入一部微短剧的基本情况（投资额、题材、集数时长、主体资质、AI 使用情况、
计划上线日期），输出：
  1. 适用性判定 —— 你这部算不算「微短剧」，归本办法管不管
  2. 分类判定   —— 一类／二类／三类，以及判定依据与临界提示
  3. 流程路径   —— 你要走哪几步，找谁办，交什么材料，多久出结果
  4. 资质核查   —— 缺什么证，怎么补，要多久，有没有替代路径
  5. 时间倒排   —— 按你的目标上线日，反推每个节点最晚什么时候动手
  6. 红线自检   —— 第二十五条11项逐条，配高频踩雷情节对照
  7. 标注自检   —— 片头标注、署名、AI 提示标识、推广物料
  8. 风险与后果 —— 不做会怎样

依据：《微短剧发展管理办法》（国家广播电视总局令第16号），2026年9月1日施行。

作者：InchStep 寸进产品实验室
"""

import datetime
from typing import Dict, Any, List, Optional

try:
    from rules import (
        REG_NAME, REG_EFFECTIVE, MAX_EPISODE_MINUTES, DEFINITION_ELEMENTS,
        DEFAULT_THRESHOLDS, THRESHOLD_NOTE, BORDERLINE_BAND, SPECIAL_SUBJECTS,
        FORBIDDEN_ITEMS, RISK_TROPES, LANGUAGE_RULES, LABEL_RULES,
        AI_LABEL_RULE, AI_LABEL_DETAIL, PROMO_RULE, PENALTIES, ENFORCEMENT_FACTS,
        LICENSE_NAME, LICENSE_REQUIREMENTS, LICENSE_REQ_NOTE, LICENSE_LEAD_DAYS,
        CLASS1_REVIEW_WORKDAYS, CLASS1_EXPERT_WORKDAYS, FILING_WORKDAYS_EXP,
        CLASS2_REVIEW_WORKDAYS_EXP, CLASS3_PLATFORM_WORKDAYS_EXP, VOLUNTARY_UPGRADE,
    )
except ImportError:
    from .rules import (  # type: ignore
        REG_NAME, REG_EFFECTIVE, MAX_EPISODE_MINUTES, DEFINITION_ELEMENTS,
        DEFAULT_THRESHOLDS, THRESHOLD_NOTE, BORDERLINE_BAND, SPECIAL_SUBJECTS,
        FORBIDDEN_ITEMS, RISK_TROPES, LANGUAGE_RULES, LABEL_RULES,
        AI_LABEL_RULE, AI_LABEL_DETAIL, PROMO_RULE, PENALTIES, ENFORCEMENT_FACTS,
        LICENSE_NAME, LICENSE_REQUIREMENTS, LICENSE_REQ_NOTE, LICENSE_LEAD_DAYS,
        CLASS1_REVIEW_WORKDAYS, CLASS1_EXPERT_WORKDAYS, FILING_WORKDAYS_EXP,
        CLASS2_REVIEW_WORKDAYS_EXP, CLASS3_PLATFORM_WORKDAYS_EXP, VOLUNTARY_UPGRADE,
    )


# ---------------------------------------------------------------------------
# 输入
# ---------------------------------------------------------------------------

def new_case() -> Dict[str, Any]:
    """一个空白项目档案。调用方按实际情况覆盖字段。"""
    return {
        "title": "",                  # 剧名（暂定名亦可）
        "producer": "",               # 制作主体名称
        "province": "",               # 属地（决定找哪个省级广电）

        # 形态
        "episodes": 0,                # 总集数
        "minutes_per_episode": 0.0,   # 单集时长（分钟）
        "is_serial": True,            # 是否故事情节连续完整、人物角色突出
        "public_broadcast": True,     # 是否面向公众播出

        # 分类要素
        "investment": 0.0,            # 总投资额（元）
        "subjects": [],               # 题材标签，含特殊题材词即触发一类
        "subject_desc": "",           # 题材／剧情一句话描述

        # 资质
        "has_production_license": False,   # 是否持《广播电视节目制作经营许可证》
        "is_broadcast_institution": False, # 是否依法设立的广播电视播出机构
        "partner_licensed": False,         # 是否已找到持证机构联合摄制／受托制作

        # 制作方式
        "uses_ai": False,             # 是否使用 AI 生成／制作（含AI换脸、AI配音、AI场景）
        "ai_scope": "",               # AI 用在哪些环节

        # 计划
        "target_launch": "",          # 目标上线日 YYYY-MM-DD
        "shooting_days": 15,          # 预计拍摄天数
        "post_days": 20,              # 预计后期天数

        # 可覆盖参数
        "thresholds": None,           # 传 dict 覆盖投资额档位
    }


# ---------------------------------------------------------------------------
# 1. 适用性判定
# ---------------------------------------------------------------------------

def check_applicability(c: Dict[str, Any]) -> Dict[str, Any]:
    mins = float(c.get("minutes_per_episode") or 0)
    hits, misses = [], []

    if 0 < mins < MAX_EPISODE_MINUTES:
        hits.append("单集时长 %.1f 分钟，少于 %d 分钟" % (mins, MAX_EPISODE_MINUTES))
    elif mins >= MAX_EPISODE_MINUTES:
        misses.append("单集时长 %.1f 分钟，已达到或超过 %d 分钟，不属于本办法所称微短剧，"
                      "应按网络剧（网络剧片）相关规定管理" % (mins, MAX_EPISODE_MINUTES))
    else:
        misses.append("未填写单集时长，无法判定")

    if c.get("is_serial"):
        hits.append("主题主线明确、故事情节连续完整、人物角色突出")
    else:
        misses.append("不具备连续完整剧情与突出人物角色，可能属于「具有微短剧特征的网络视听内容」，"
                      "由播出单位按第三十三条第（三）项履行内容管理职责")

    if c.get("public_broadcast"):
        hits.append("通过互联网站／应用程序／分发平台等渠道面向公众播出")
    else:
        misses.append("非面向公众播出")

    applies = len(misses) == 0
    return {"applies": applies, "hits": hits, "misses": misses,
            "elements": DEFINITION_ELEMENTS}


# ---------------------------------------------------------------------------
# 2. 分类判定
# ---------------------------------------------------------------------------

def classify(c: Dict[str, Any]) -> Dict[str, Any]:
    th = dict(DEFAULT_THRESHOLDS)
    if c.get("thresholds"):
        th.update(c["thresholds"])

    inv = float(c.get("investment") or 0)
    subj_text = " ".join(list(c.get("subjects") or [])) + " " + str(c.get("subject_desc") or "")
    matched_special = [s for s in SPECIAL_SUBJECTS if s in subj_text]

    reasons: List[str] = []
    borderline: List[str] = []

    if matched_special:
        category = 1
        reasons.append("主要剧情涉及特殊题材（%s），依第五条直接归为一类，与投资额无关"
                       % "、".join(matched_special))
    elif inv >= th["class1_min"]:
        category = 1
        reasons.append("投资额 %s 元，达到「投资额度较大」参考档位（≥%s 元）"
                       % (_num(inv), _num(th["class1_min"])))
    elif inv >= th["class2_min"]:
        category = 2
        reasons.append("投资额 %s 元，属「投资额度相对不大」区间（%s ~ %s 元），且为一般题材"
                       % (_num(inv), _num(th["class2_min"]), _num(th["class1_min"])))
    else:
        category = 3
        reasons.append("投资额 %s 元，属「投资额度较低」区间（<%s 元），且为一般题材"
                       % (_num(inv), _num(th["class2_min"])))

    # 临界提示：只在非特殊题材（即由投资额决定类别）时才有意义
    if not matched_special:
        for name, val in (("一类／二类分界", th["class1_min"]), ("二类／三类分界", th["class2_min"])):
            lo, hi = val * (1 - BORDERLINE_BAND), val * (1 + BORDERLINE_BAND)
            if lo <= inv <= hi:
                borderline.append(
                    "投资额 %s 元落在%s（%s 元）上下 %d%% 的临界带内，"
                    "建议在立项阶段就向属地广电主管部门书面确认适用类别，不要自行推定。"
                    % (_num(inv), name, _num(val), int(BORDERLINE_BAND * 100)))

    return {"category": category, "reasons": reasons, "borderline": borderline,
            "matched_special": matched_special, "thresholds": th,
            "threshold_note": THRESHOLD_NOTE}


def _num(v: Any) -> str:
    try:
        return "{:,.0f}".format(float(v))
    except (TypeError, ValueError):
        return str(v)


# ---------------------------------------------------------------------------
# 3. 资质核查
# ---------------------------------------------------------------------------

def check_qualification(c: Dict[str, Any], category: int) -> Dict[str, Any]:
    need_license = category in (1, 2)
    has = bool(c.get("has_production_license")) or bool(c.get("is_broadcast_institution"))
    blocking = need_license and not has and not c.get("partner_licensed")

    notes: List[str] = []
    paths: List[str] = []

    if not need_license:
        notes.append("三类微短剧不以持有%s为备案前提，由符合条件的播出单位履行播前审核并标注节目编号。"
                     % LICENSE_NAME)
        notes.append("但制作方仍需对内容合规负责；若后续想自愿升级为一类／二类申报，"
                     "届时资质要求同样适用。")
    elif has:
        which = LICENSE_NAME if c.get("has_production_license") else "广播电视播出机构资质"
        notes.append("已具备%s，满足第十四条对申报主体的要求。" % which)
    elif c.get("partner_licensed"):
        notes.append("本方未持证，但已安排与持证机构合作。注意：备案与报审的申报主体必须是持证方，"
                     "联合摄制协议中要把署名、著作权归属、报审主体三件事写清楚，避免拿证后扯皮。")
    else:
        notes.append("这是本次自检最关键的阻断项：一类／二类的备案公示与报审，"
                     "申报主体必须是持有%s的制作机构，或依法设立的广播电视播出机构。" % LICENSE_NAME)
        paths.append("路径一 自行办证：门槛为 %s。%s 从申请到拿证约需 2~3 个月，"
                     "若目标上线日临近，这条路大概率赶不上。"
                     % ("；".join(LICENSE_REQUIREMENTS), LICENSE_REQ_NOTE))
        paths.append("路径二 与持证机构合作：由持证方作为备案与报审主体，本方以联合摄制或"
                     "受托制作身份参与。这是时间紧时的现实选择，代价是主体署名与部分权利让渡。")
        paths.append("路径三 调整立项规模／题材，使项目落入三类：仅在投资额与题材确实可调时成立，"
                     "不能靠拆分合同、压低报账金额做数字游戏——投资额与实际制作规模明显背离的，"
                     "属地核查时容易被认定为规避监管。")

    return {"need_license": need_license, "satisfied": has or bool(c.get("partner_licensed")),
            "blocking": blocking, "notes": notes, "paths": paths,
            "license_name": LICENSE_NAME, "requirements": LICENSE_REQUIREMENTS}


# ---------------------------------------------------------------------------
# 4. 流程路径
# ---------------------------------------------------------------------------

def build_workflow(category: int, c: Dict[str, Any]) -> List[Dict[str, str]]:
    """返回按时间顺序排列的流程节点。"""
    steps: List[Dict[str, str]] = []

    if category == 1:
        steps.append({
            "阶段": "拍摄前", "事项": "备案公示申请",
            "找谁": "省、自治区、直辖市以上人民政府广播电视主管部门（直接申报机构报总局）",
            "材料": "《微短剧备案公示申请表》、剧情梗概",
            "时限": "无法定时限，经验约 %d 个工作日；特殊题材需征求有关主管部门意见，另需时间"
                    % FILING_WORKDAYS_EXP,
            "依据": "第十二条、第十四条",
        })
        steps.append({
            "阶段": "拍摄前", "事项": "总局上网公示",
            "找谁": "国务院广播电视主管部门",
            "材料": "由省级审核后报请公示，公示内容含剧名、制作机构",
            "时限": "公示完成后方可开机",
            "依据": "第十四条",
        })
        steps.append({
            "阶段": "拍摄中", "事项": "按备案内容拍摄",
            "找谁": "—",
            "材料": "—",
            "时限": "变更主要人物定位或故事整体走向的，须重新履行备案手续；"
                    "仅变更剧名、制作机构的，办理变更手续即可",
            "依据": "第十六条",
        })
        steps.append({
            "阶段": "播出前", "事项": "内容审核与发行许可",
            "找谁": "省、自治区、直辖市以上人民政府广播电视主管部门",
            "材料": "《一类微短剧报审表》；%s或《广播电视播出机构许可证》；"
                    "图像声音字幕时码符合要求的样片；片头片尾和歌曲字幕表；"
                    "聘用境外人员的批准文件复印件（如有）" % LICENSE_NAME,
            "时限": "自受理起 %d 日内作出决定，其中专家评审 %d 日；需修改的，改后重新送审"
                    % (CLASS1_REVIEW_WORKDAYS, CLASS1_EXPERT_WORKDAYS),
            "依据": "第十七条、第十九条、第二十条",
        })
        steps.append({
            "阶段": "播出前", "事项": "取得《微短剧发行许可证》",
            "找谁": "省级以上广电主管部门颁发，证件由总局统一印制",
            "材料": "—",
            "时限": "无证不得播出、不得参加评奖评优",
            "依据": "第十七条",
        })

    elif category == 2:
        steps.append({
            "阶段": "拍摄前", "事项": "备案公示（参照一类执行）",
            "找谁": "省、自治区、直辖市人民政府广播电视主管部门",
            "材料": "参照《微短剧备案公示申请表》、剧情梗概；各省可另有实施细则",
            "时限": "办法规定二类「可以参照适用」一类备案公示制度，具体以本省细则为准；"
                    "经验约 %d 个工作日" % FILING_WORKDAYS_EXP,
            "依据": "第十二条、第十三条",
        })
        steps.append({
            "阶段": "播出前", "事项": "内容审核与审批",
            "找谁": "省、自治区、直辖市以上人民政府广播电视主管部门",
            "材料": "参照一类报审材料，各省鼓励简化",
            "时限": "办法鼓励各省优化流程、简化材料、提高时效；经验约 %d 个工作日"
                    % CLASS2_REVIEW_WORKDAYS_EXP,
            "依据": "第十七条、第二十四条",
        })
        steps.append({
            "阶段": "播出前", "事项": "取得省级批准文件",
            "找谁": "省、自治区、直辖市人民政府广播电视主管部门",
            "材料": "—",
            "时限": "批准文件编号规则由总局统一制定；无批准文件不得播出、不得参评",
            "依据": "第十七条",
        })

    else:
        steps.append({
            "阶段": "播出前", "事项": "播出单位播前审核",
            "找谁": "符合条件的播出平台（履行内容管理职责的主体）",
            "材料": "成片、剧情说明等平台要求的送审材料",
            "时限": "经验约 %d 个工作日，各平台不同" % CLASS3_PLATFORM_WORKDAYS_EXP,
            "依据": "第十七条、第三十三条",
        })
        steps.append({
            "阶段": "播出前", "事项": "标注节目编号并线上报备",
            "找谁": "播出单位向广电主管部门线上系统报送剧目信息与节目编号",
            "材料": "剧目信息、节目编号",
            "时限": "非独播的，各播出单位须按各自审核版本标注本平台编号，不得共用他方编号",
            "依据": "第三十三条第（二）项",
        })
        steps.append({
            "阶段": "重播时", "事项": "重新审核",
            "找谁": "播出单位",
            "材料": "—",
            "时限": "重新播出的三类微短剧，应当依照办法规定的审核标准重新审核",
            "依据": "第三十五条",
        })

    return steps


# ---------------------------------------------------------------------------
# 5. 时间倒排
# ---------------------------------------------------------------------------

def _minus_workdays(d: datetime.date, n: int) -> datetime.date:
    """从 d 往前推 n 个工作日（仅剔除周末，未计法定节假日）。"""
    cur = d
    left = n
    while left > 0:
        cur -= datetime.timedelta(days=1)
        if cur.weekday() < 5:
            left -= 1
    return cur


def _plus_workdays(d: datetime.date, n: int) -> datetime.date:
    """从 d 往后推 n 个工作日（仅剔除周末，未计法定节假日）。"""
    cur = d
    left = n
    while left > 0:
        cur += datetime.timedelta(days=1)
        if cur.weekday() < 5:
            left -= 1
    return cur


def earliest_feasible_launch(c: Dict[str, Any], category: int,
                             qual: Dict[str, Any],
                             start: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    从今天正推，算出这个项目最早能在哪天合规上线。
    倒排告诉你来不及，这里回答最早什么时候来得及——后者才是能拿去改排期的东西。
    """
    cur = start or datetime.date.today()
    path: List[Dict[str, str]] = []

    if qual.get("need_license") and not qual.get("satisfied"):
        cur = cur + datetime.timedelta(days=LICENSE_LEAD_DAYS)
        path.append({"节点": "取得%s" % LICENSE_NAME, "预计完成": cur.isoformat(),
                     "耗时": "约 %d 天（经验下限，实际常需 2~3 个月）" % LICENSE_LEAD_DAYS})

    if category in (1, 2):
        cur = _plus_workdays(cur, FILING_WORKDAYS_EXP)
        path.append({"节点": "备案公示获批", "预计完成": cur.isoformat(),
                     "耗时": "约 %d 个工作日（经验值；特殊题材需征求有关方面意见，会更长）"
                             % FILING_WORKDAYS_EXP})

    shoot = int(c.get("shooting_days") or 0)
    if shoot > 0:
        cur = cur + datetime.timedelta(days=shoot)
        path.append({"节点": "拍摄完成", "预计完成": cur.isoformat(), "耗时": "%d 天" % shoot})

    post = int(c.get("post_days") or 0)
    if post > 0:
        cur = cur + datetime.timedelta(days=post)
        path.append({"节点": "后期完成，出送审样片", "预计完成": cur.isoformat(),
                     "耗时": "%d 天" % post})

    if category == 1:
        cur = _plus_workdays(cur, CLASS1_REVIEW_WORKDAYS + 10)
        path.append({"节点": "取得《微短剧发行许可证》", "预计完成": cur.isoformat(),
                     "耗时": "法定 %d 日内出结果，另留 10 个工作日应对一次修改重审"
                             % CLASS1_REVIEW_WORKDAYS})
    elif category == 2:
        cur = _plus_workdays(cur, CLASS2_REVIEW_WORKDAYS_EXP)
        path.append({"节点": "取得省级批准文件", "预计完成": cur.isoformat(),
                     "耗时": "约 %d 个工作日（经验值，各省不同）" % CLASS2_REVIEW_WORKDAYS_EXP})
    else:
        cur = _plus_workdays(cur, CLASS3_PLATFORM_WORKDAYS_EXP)
        path.append({"节点": "平台播前审核通过并取得节目编号", "预计完成": cur.isoformat(),
                     "耗时": "约 %d 个工作日（经验值，各平台不同）" % CLASS3_PLATFORM_WORKDAYS_EXP})

    path.append({"节点": "可合规上线", "预计完成": cur.isoformat(), "耗时": "—"})
    return {"date": cur, "path": path}


def build_timeline(c: Dict[str, Any], category: int,
                   qual: Dict[str, Any]) -> Dict[str, Any]:
    """按目标上线日倒推各节点最晚启动日。"""
    raw = (c.get("target_launch") or "").strip()
    if not raw:
        return {"available": False, "nodes": [], "warnings": ["未填写目标上线日，跳过倒排期。"]}
    try:
        launch = datetime.datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return {"available": False, "nodes": [],
                "warnings": ["目标上线日格式应为 YYYY-MM-DD，当前值：%s" % raw]}

    today = datetime.date.today()
    nodes: List[Dict[str, str]] = []
    warnings: List[str] = []
    cursor = launch

    nodes.append({"节点": "目标上线播出", "最晚日期": launch.isoformat(), "说明": "以此日倒推"})

    if category == 1:
        cursor = _minus_workdays(cursor, CLASS1_REVIEW_WORKDAYS)
        nodes.append({"节点": "最晚送审日（申请内容审核与发行许可）",
                      "最晚日期": cursor.isoformat(),
                      "说明": "法定 %d 日内出结果，含专家评审 %d 日；此处按工作日推算，"
                              "未计入需修改重审的情形"
                              % (CLASS1_REVIEW_WORKDAYS, CLASS1_EXPERT_WORKDAYS)})
        buf = _minus_workdays(cursor, 10)
        nodes.append({"节点": "建议送审日（含一次修改重审缓冲）",
                      "最晚日期": buf.isoformat(),
                      "说明": "第二十条规定需修改的须改后重新送审，且第二十一条禁止转移送审，"
                              "务必留出返工余量"})
        cursor = buf
    elif category == 2:
        cursor = _minus_workdays(cursor, CLASS2_REVIEW_WORKDAYS_EXP)
        nodes.append({"节点": "最晚送审日（省级审核审批）",
                      "最晚日期": cursor.isoformat(),
                      "说明": "经验值 %d 个工作日，各省不同，以本省细则为准"
                              % CLASS2_REVIEW_WORKDAYS_EXP})
    else:
        cursor = _minus_workdays(cursor, CLASS3_PLATFORM_WORKDAYS_EXP)
        nodes.append({"节点": "最晚交平台送审日",
                      "最晚日期": cursor.isoformat(),
                      "说明": "平台播前审核 + 标注节目编号 + 线上报备，经验值 %d 个工作日"
                              % CLASS3_PLATFORM_WORKDAYS_EXP})

    post = int(c.get("post_days") or 0)
    if post > 0:
        cursor = cursor - datetime.timedelta(days=post)
        nodes.append({"节点": "最晚后期完成日（出送审样片）",
                      "最晚日期": cursor.isoformat(),
                      "说明": "样片须图像、声音、字幕、时码符合审核要求，不是粗剪能交的"})

    shoot = int(c.get("shooting_days") or 0)
    if shoot > 0:
        cursor = cursor - datetime.timedelta(days=shoot)
        nodes.append({"节点": "最晚开机日", "最晚日期": cursor.isoformat(),
                      "说明": "拍摄周期 %d 天" % shoot})

    if category in (1, 2):
        cursor = _minus_workdays(cursor, FILING_WORKDAYS_EXP)
        nodes.append({"节点": "最晚备案公示申请日",
                      "最晚日期": cursor.isoformat(),
                      "说明": "备案公示须在开机前完成；一类经省级审核后报总局公示，"
                              "特殊题材还需征求有关方面意见，时间更长"})

    if qual.get("need_license") and not qual.get("satisfied"):
        lic = cursor - datetime.timedelta(days=LICENSE_LEAD_DAYS)
        nodes.append({"节点": "最晚启动%s申请日" % LICENSE_NAME,
                      "最晚日期": lic.isoformat(),
                      "说明": "办证经验周期 2~3 个月，此处按下限 %d 天推算" % LICENSE_LEAD_DAYS})
        cursor = lic

    feasible: Dict[str, Any] = {}
    if cursor < today:
        feasible = earliest_feasible_launch(c, category, qual, today)
        warnings.append(
            "按上述倒排，最早节点应在 %s 启动，而今天已是 %s——目标上线日 %s 在合规流程上已不可达。"
            % (cursor.isoformat(), today.isoformat(), launch.isoformat()))
        warnings.append(
            "从今天算起正推，本项目最早可合规上线日为 %s（比原计划晚 %d 天）。"
            "若必须守住原档期，现实做法只有两条：由已持证机构作为备案与报审主体接手申报，"
            "或在投资额与题材确实可调的前提下重新评估项目类别。"
            % (feasible["date"].isoformat(), (feasible["date"] - launch).days))
    else:
        warnings.append("按上述倒排，距最早节点还有 %d 天，排期可行。" % (cursor - today).days)

    eff = datetime.date(2026, 9, 1)
    if launch >= eff:
        warnings.append("目标上线日在 %s 及以后，%s 已施行，上述流程为强制要求。"
                        % (REG_EFFECTIVE, REG_NAME))
    else:
        warnings.append("目标上线日早于 %s。办法虽尚未施行，但备案与审核体系此前已在运行，"
                        "且跨越施行日的项目仍会被按新规核查，建议按新规准备。" % REG_EFFECTIVE)

    return {"available": True, "nodes": nodes, "warnings": warnings,
            "feasible": feasible}


# ---------------------------------------------------------------------------
# 总装：一次跑完全流程
# ---------------------------------------------------------------------------

try:
    from checker_part2 import (
        build_content_checklist, build_label_checklist, build_risks,
        assemble, CATEGORY_NAME, CATEGORY_GATE,
    )
except ImportError:
    from .checker_part2 import (  # type: ignore
        build_content_checklist, build_label_checklist, build_risks,
        assemble, CATEGORY_NAME, CATEGORY_GATE,
    )


def run(c: Dict[str, Any]) -> Dict[str, Any]:
    """输入项目档案，输出完整自检结果。"""
    applic = check_applicability(c)

    # 不适用本办法（如单集≥20分钟、缺乏连续完整剧情）时短路：跳过分类/资质/流程/倒排，
    # 仅保留红线自检与适用性结论，避免给出一套根本用不上的流程。
    if not applic["applies"]:
        cls = {
            "category": 0,
            "reasons": ["单集时长达到或超过 %d 分钟，或缺乏连续完整剧情与突出人物角色，"
                        "不属于本办法所称微短剧，应按网络剧（网络剧片）相关规定管理；"
                        "本办法的备案、审核、许可证、节目编号要求不适用。" % MAX_EPISODE_MINUTES],
            "borderline": [],
            "matched_special": [],
            "thresholds": dict(DEFAULT_THRESHOLDS),
            "threshold_note": THRESHOLD_NOTE,
            "not_applicable": True,
        }
        qual = {
            "need_license": False, "satisfied": False, "blocking": False,
            "notes": ["本项目不适用《微短剧发展管理办法》，无备案、审核、许可证、节目编号等要求；"
                      "请按网络剧（网络剧片）的备案与审核规定另行办理。"],
            "paths": [], "license_name": LICENSE_NAME, "requirements": LICENSE_REQUIREMENTS,
        }
        steps: List[Dict[str, str]] = []
        tl = {"available": False, "nodes": [], "warnings": ["不适用本办法，不生成倒排期。"],
              "feasible": {}}
        content = build_content_checklist(c)
        labels = {"items": [], "language": list(LANGUAGE_RULES),
                  "promo": PROMO_RULE, "ai": None,
                  "note": "不适用本办法，标注与 AI 标识要求不在此列。"}
        risks = build_risks(0, qual, applic)
        return assemble(c, applic, cls, qual, steps, tl, content, labels, risks)

    cls = classify(c)
    category = cls["category"]
    qual = check_qualification(c, category)
    steps = build_workflow(category, c)
    tl = build_timeline(c, category, qual)
    content = build_content_checklist(c)
    labels = build_label_checklist(c, category)
    risks = build_risks(category, qual, applic)
    return assemble(c, applic, cls, qual, steps, tl, content, labels, risks)


# ---------------------------------------------------------------------------
# 文本报告（终端速览）
# ---------------------------------------------------------------------------

def to_report(r: Dict[str, Any]) -> str:
    c = r["case"]
    L: List[str] = []
    L.append("=" * 68)
    L.append("微短剧合规自检报告　%s" % (c.get("title") or "（未命名项目）"))
    L.append("=" * 68)
    L.append("依据：%s，%s施行" % (r["reg_name"], r["reg_effective"]))
    L.append("")

    L.append("【一】适用性判定")
    ap = r["applicability"]
    L.append("　结论：%s" % ("适用本办法" if ap["applies"] else "不适用或存疑，见下"))
    for h in ap["hits"]:
        L.append("　　符合：%s" % h)
    for m in ap["misses"]:
        L.append("　　不符：%s" % m)
    L.append("")

    L.append("【二】分类判定")
    L.append("　结论：%s" % r["category_name"])
    L.append("　准入：%s" % r["gate"])
    for x in r["classification"]["reasons"]:
        L.append("　　依据：%s" % x)
    for b in r["classification"]["borderline"]:
        L.append("　　临界：%s" % b)
    L.append("")

    L.append("【三】主体资质")
    q = r["qualification"]
    L.append("　需要资质：%s；当前满足：%s" % ("是" if q["need_license"] else "否",
                                          "是" if q["satisfied"] else "否"))
    for n in q["notes"]:
        L.append("　　%s" % n)
    for p in q["paths"]:
        L.append("　　可选：%s" % p)
    L.append("")

    L.append("【四】流程路径")
    for i, s in enumerate(r["workflow"], 1):
        L.append("　%d. [%s] %s" % (i, s["阶段"], s["事项"]))
        L.append("　　　找谁：%s" % s["找谁"])
        L.append("　　　材料：%s" % s["材料"])
        L.append("　　　时限：%s" % s["时限"])
        L.append("　　　依据：%s" % s["依据"])
    L.append("")

    L.append("【五】时间倒排")
    tl = r["timeline"]
    if tl["available"]:
        for n in tl["nodes"]:
            L.append("　%s　%s" % (n["最晚日期"], n["节点"]))
    for w in tl["warnings"]:
        L.append("　提示：%s" % w)
    if tl.get("feasible"):
        L.append("　最早可行上线路径（从今天正推）：")
        for n in tl["feasible"]["path"]:
            L.append("　　%s　%s" % (n["预计完成"], n["节点"]))
    L.append("")

    L.append("【六】内容红线自检（第二十五条，共11项）")
    for idx, text, _ in r["content"]["rows"]:
        L.append("　%s %s" % (idx, text[:40] + ("…" if len(text) > 40 else "")))
    if r["content"]["hit_tropes"]:
        L.append("　本项目题材关联的高频踩雷点：")
        for t, item, why in r["content"]["hit_tropes"]:
            L.append("　　· %s → %s（%s）" % (t, item, why))
    L.append("")

    L.append("【七】标注与AI提示")
    for it in r["labels"]["items"]:
        L.append("　· %s" % it)
    if r["labels"]["ai"]:
        L.append("　AI标识（第三十四条）：%s" % r["labels"]["ai"]["rule"])
        for d in r["labels"]["ai"]["detail"]:
            L.append("　　- %s" % d)
    L.append("")

    L.append("【八】风险清单")
    for rk in r["risks"]:
        L.append("　[%s] %s" % (rk["等级"], rk["风险点"]))
        L.append("　　后果：%s" % rk["后果"])
    L.append("")
    L.append("=" * 68)
    return "\n".join(L)


# ---------------------------------------------------------------------------
# A4 版式 HTML 报告
# ---------------------------------------------------------------------------

def to_html_report(r: Dict[str, Any], out_path: str) -> str:
    try:
        from report import render_html, save_html
    except ImportError:
        from .report import render_html, save_html  # type: ignore

    c = r["case"]
    ap, cls, q, tl = r["applicability"], r["classification"], r["qualification"], r["timeline"]

    meta = [
        ("剧名", c.get("title") or "（未命名）"),
        ("制作主体", c.get("producer") or "（未填写）"),
        ("属地", c.get("province") or "（未填写）"),
        ("体量", "%s集 × 单集%s分钟" % (c.get("episodes") or "—",
                                     c.get("minutes_per_episode") or "—")),
        ("投资额", "%s 元" % _num(c.get("investment") or 0)),
        ("判定结论", r["category_name"]),
        ("适用法规", r["reg_name"]),
    ]

    secs: List[Dict[str, Any]] = []

    # 一、结论
    if not ap["applies"]:
        concl = "本项目不适用《微短剧发展管理办法》（%s）。%s" % (
            r["reg_name"],
            (q.get("notes") or [""])[0])
    else:
        concl = "本项目判定为%s。播出前必须取得：%s。" % (r["category_name"], r["gate"])
        if q.get("blocking"):
            concl += "　当前存在阻断项：申报主体尚不具备%s，须先解决资质问题，否则备案环节即无法受理。" % q["license_name"]
    secs.append({"kind": "callout", "label": "自检结论", "body": concl})

    # 二、适用性
    ap_rows = [["符合", h] for h in ap["hits"]] + [["不符", m] for m in ap["misses"]]
    secs.append({"kind": "table", "title": "一、适用性判定（第二条）",
                 "headers": ["判定", "说明"], "rows": ap_rows})

    # 三、分类
    cl_rows = [["判定依据", x] for x in cls["reasons"]]
    for b in cls["borderline"]:
        cl_rows.append(["临界提示", b])
    cl_rows.append(["投资额档位说明", cls["threshold_note"]])
    secs.append({"kind": "table", "title": "二、分类判定（第五条）",
                 "headers": ["项目", "内容"], "rows": cl_rows})
    if r.get("upgrade_note"):
        secs.append({"kind": "callout", "label": "可选：自愿升级申报", "body": r["upgrade_note"]})

    # 四、资质
    qrows = [["是否需要", "是" if q["need_license"] else "否"],
             ["当前是否满足", "是" if q["satisfied"] else "否"]]
    for n in q["notes"]:
        qrows.append(["说明", n])
    for p in q["paths"]:
        qrows.append(["可选路径", p])
    secs.append({"kind": "table", "title": "三、主体资质核查（第十四条）",
                 "headers": ["项目", "内容"], "rows": qrows})

    # 五、流程
    wrows = [[s["阶段"], s["事项"], s["找谁"], s["材料"], s["时限"], s["依据"]]
             for s in r["workflow"]]
    secs.append({"kind": "table", "title": "四、你需要走的流程",
                 "headers": ["阶段", "事项", "受理部门", "提交材料", "时限", "条文依据"],
                 "rows": wrows})

    # 六、倒排
    if tl["available"]:
        secs.append({"kind": "table", "title": "五、按目标上线日倒排的关键节点",
                     "headers": ["最晚日期", "节点", "说明"],
                     "rows": [[n["最晚日期"], n["节点"], n["说明"]] for n in tl["nodes"]]})
    for w in tl["warnings"]:
        secs.append({"kind": "callout", "label": "排期提示", "body": w})
    if tl.get("feasible"):
        secs.append({"kind": "table", "title": "五之二、从今天正推的最早可行上线路径",
                     "headers": ["节点", "预计完成", "耗时"],
                     "rows": [[n["节点"], n["预计完成"], n["耗时"]]
                              for n in tl["feasible"]["path"]]})

    # 七、红线自检表
    secs.append({"kind": "table", "title": "六、内容红线逐条自检（第二十五条）",
                 "headers": ["条项", "禁止内容", "自检"],
                 "rows": r["content"]["rows"]})
    secs.append({"kind": "table", "title": "七、高频踩雷情节对照",
                 "headers": ["常见写法", "对应条项", "为什么会被卡"],
                 "rows": [[t, i, w] for t, i, w in r["content"]["tropes"]]})
    if r["content"]["hit_tropes"]:
        body = "；".join("%s（%s）" % (t, w) for t, _, w in r["content"]["hit_tropes"])
        secs.append({"kind": "callout", "label": "与本项目题材直接相关的风险点", "body": body})

    # 八、标注
    secs.append({"kind": "list", "title": "八、信息标注自检（第二十七条）",
                 "items": r["labels"]["items"]})
    secs.append({"kind": "list", "title": "九、剧名台词字幕规范（第二十六条）",
                 "items": r["labels"]["language"]})
    if r["labels"]["ai"]:
        ai = r["labels"]["ai"]
        secs.append({"kind": "callout", "label": "AI 制作提示标识（第三十四条）", "body": ai["rule"]})
        secs.append({"kind": "list", "title": "十、AI 标识落地要点",
                     "items": ai["detail"] + ["本项目 AI 使用环节：%s" % ai["scope"]]})
        secs.append({"kind": "callout", "label": "工作流建议",
                     "body": "标识最好在成片输出环节由制作工具统一写入，而不是剪完之后逐集手工叠加。"
                             "一部 80 集的剧手工加标识，漏一集就是一集的播出风险，而且隐式元数据"
                             "靠人工基本补不齐。挑 AI 短剧制作工具时，不妨把「能否在导出环节批量"
                             "嵌入显式标识与元数据」直接列进选型清单。"})
    secs.append({"kind": "callout", "label": "推广物料（第二十八条）", "body": r["labels"]["promo"]})

    # 九、风险
    secs.append({"kind": "table", "title": "十一、风险清单与后果",
                 "headers": ["等级", "风险点", "后果"],
                 "rows": [[x["等级"], x["风险点"], x["后果"]] for x in r["risks"]]})
    secs.append({"kind": "table", "title": "十二、罚则速查",
                 "headers": ["条文", "情形", "后果"],
                 "rows": [[a, b, cc] for a, b, cc in r["penalties"]]})
    secs.append({"kind": "list", "title": "十三、已发生的执法事实",
                 "items": r["enforcement"]})

    disclaimer = (
        "本报告依据%s及公开政策资料，按用户填报信息自动生成，用于项目自查与流程准备，"
        "不构成法律意见，也不能替代广播电视主管部门的正式审核结论。"
        "办法第五条明确分类标准由国务院广播电视主管部门另行制定并适时调整，"
        "报告中的投资额档位、备案与审核经验时限均为参考值，不同省份实施细则存在差异。"
        "涉及立项决策、资质安排与送审时间的，请以属地广播电视主管部门的书面答复为准。"
        % r["reg_name"]
    )
    html = render_html(
        title="微短剧合规自检与备案指引报告",
        subtitle="%s　|　判定结论：%s" % (c.get("title") or "未命名项目", r["category_name"]),
        meta=meta, sections=secs, disclaimer=disclaimer,
        footer_note="本报告由合规判定引擎按《微短剧发展管理办法》条文自动生成")
    return save_html(html, out_path)
