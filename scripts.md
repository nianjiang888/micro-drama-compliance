# 引擎结构与参数说明

本技能的判定逻辑全部用纯标准库 Python 实现，没有第三方依赖，也没有网络调用。
包内不含任何 IP、密钥、绝对路径，可直接上架。

## 文件结构

```
micro-drama-compliance-1.0.0/
├── SKILL.md              # 技能说明与触发词（frontmatter 含 pricing/deliverable）
├── regulation.md         # 16 号令关键条文速查，按「判什么看哪条」重组
├── workflow.md           # 三类微短剧的完整流程、材料、时限对照
├── examples.md           # 四个实跑案例
├── scripts.md            # 本文件：引擎结构与参数覆盖
├── disclaimer.md         # 免责声明与使用边界
├── sample-report.html    # 案例一的真实报告样例（A4 版式）
└── scripts/
    ├── rules.py          # 法条数据化：常量与映射表，与判定引擎分离，便于政策调整
    ├── checker.py        # 判定/流程/倒排/总装 + 终端文本报告 + A4 HTML 报告
    ├── checker_part2.py  # 自检清单/标注/风险/总装/报告输出（拆出以免单文件过长）
    ├── report.py         # 纯标准库 A4 HTML 渲染器（与判定逻辑解耦）
    ├── _selftest.py      # 内部自测脚本，验证四个案例判定，打包前删除
    └── _gen_sample.py    # 内部样例生成脚本，打包前删除
```

`_selftest.py` 与 `_gen_sample.py` 文件名以下划线开头，明确是开发期脚本，上架时从包中剔除。

## 数据流

```
用户填报字段（new_case 字典）
        │
        ▼
check_applicability() ──不适用──▶ 短路：仅返回适用性结论 + 红线自检，不跑分类/资质/流程
        │适用
        ▼
classify()            ── 题材优先于投资额，输出 category 1/2/3 + 临界带提示
        ▼
check_qualification() ── 一类/二类需持证，无证据阻断项，给三条路径
        ▼
build_workflow()      ── 三类各自的流程节点（找谁/材料/时限/依据）
        ▼
build_timeline()      ── 按目标上线日倒排；不可达时调用 earliest_feasible_launch() 正推最早可行日
        ▼
build_content_checklist / build_label_checklist / build_risks
        ▼
assemble() + to_report() / to_html_report()
```

## 关键函数

| 函数 | 位置 | 作用 |
|---|---|---|
| `new_case()` | checker.py | 返回空白项目档案字典 |
| `run(c)` | checker.py | 总装入口，一次跑完全流程返回结果字典 `r` |
| `to_report(r)` | checker.py | 终端文本速览 |
| `to_html_report(r, out_path)` | checker.py | 生成 A4 HTML 报告 |
| `check_applicability(c)` | checker.py | 第二条适用性判定 |
| `classify(c)` | checker.py | 第五条三类分类，题材优先 |
| `check_qualification(c, cat)` | checker.py | 第十四条资质核查 |
| `build_workflow(cat, c)` | checker.py | 流程节点表 |
| `build_timeline(c, cat, qual)` | checker.py | 倒排 + 最早可行路径 |
| `earliest_feasible_launch(...)` | checker.py | 从今天正推最早合规上线日 |
| `build_content_checklist(c)` | checker_part2.py | 25 条 11 项红线自检 + 题材踩雷匹配 |
| `build_label_checklist(c, cat)` | checker_part2.py | 标注 / AI 标识自检 |
| `build_risks(cat, qual, ap)` | checker_part2.py | 风险分级清单 |
| `assemble(...)` | checker_part2.py | 把各部分装进结果字典 |

## 项目档案字段（new_case 字典）

| 字段 | 含义 | 影响 |
|---|---|---|
| `title` / `producer` / `province` | 剧名 / 制作主体 / 属地省份 | 报告抬头与属地提示 |
| `episodes` / `minutes_per_episode` | 总集数 / 单集时长 | 适用性判定（单集 ≥20 分钟直接不适用） |
| `is_serial` / `public_broadcast` | 是否连续完整剧情 / 是否面向公众 | 适用性判定 |
| `investment` | 总投资额 | 三类分类的核心输入之一 |
| `subjects` / `subject_desc` | 题材标签 / 一句话剧情 | 特殊题材命中、踩雷情节匹配 |
| `has_production_license` | 是否持证 | 一类/二类资质阻断判定 |
| `is_broadcast_institution` | 是否播出机构 | 资质替代路径 |
| `partner_licensed` | 是否安排与持证方合作 | 资质替代路径 |
| `uses_ai` / `ai_scope` | 是否用 AI / 使用环节 | 触发第三十四条标识块 |
| `target_launch` | 目标上线日 `YYYY-MM-DD` | 倒排起点 |
| `shooting_days` / `post_days` | 拍摄天数 / 后期天数 | 倒排与正推 |

## 参数覆盖（按本省细则调整）

`rules.py` 把可机器判定的条款抽成常量，改政策或本省细则时只动这里，不动引擎：

- `MAX_EPISODE_MINUTES = 20`：单集时长线（第二条）。
- `DEFAULT_THRESHOLDS = {"class1_min": 3000000, "class2_min": 1000000}`：投资额档位**参考值**，非法条数字。条文本身无金额，档位由国务院广电主管部门另行制定并适时调整。
- `BORDERLINE_BAND = 0.20`：临界带宽度，投资额落在阈值 ±20% 时报告单独提示书面确认。
- `SPECIAL_SUBJECTS`：九类特殊题材关键词（政治/军事/外交/国家安全/统战/民族/宗教/司法/公安）。
- `FORBIDDEN_ITEMS`：第二十五条 11 项红线原文。
- `RISK_TROPES`：高频踩雷情节 → 条项映射，引擎按题材关键词匹配。
- `LICENSE_REQUIREMENTS` / `LICENSE_LEAD_DAYS`：持证门槛与办证经验周期。
- `CLASS1_REVIEW_WORKDAYS` / `FILING_WORKDAYS_EXP` / `CLASS2_REVIEW_WORKDAYS_EXP` / `CLASS3_PLATFORM_WORKDAYS_EXP`：各类审核/备案/平台经验时限（标注「经验值」，非法定）。

**调用方覆盖档位**：`new_case()` 的 `thresholds` 字段可整体或部分覆盖内置档位，例如某省细则把三类线提到 150 万：

```python
c["thresholds"] = {"class2_min": 1500000}
```

其余时限常量如需按省调整，直接改 `rules.py` 即可，引擎无需改动。

## 怎么运行

```bash
cd scripts
python -c "
from checker import new_case, run, to_report, to_html_report
c = new_case()
c.update({
    'title': '剧名', 'producer': '制作方', 'province': '广东省',
    'episodes': 80, 'minutes_per_episode': 2.0,
    'investment': 280000, 'subjects': ['都市','重生'],
    'subject_desc': '一句话剧情',
    'has_production_license': False,
    'uses_ai': True, 'ai_scope': 'AI生成场景、AI配音',
    'target_launch': '2026-10-20', 'shooting_days': 5, 'post_days': 10,
})
r = run(c)
print(to_report(r))
to_html_report(r, '../合规自检报告.html')
"
```

## 怎么扩展

- 新增红线条目：往 `rules.py` 的 `FORBIDDEN_ITEMS` 加元组 `(条项, 原文)`。
- 调整踩雷关键词：改 `checker_part2.py` 的 `_trope_keywords` 关键词表。
- 调整各省时限：改 `rules.py` 对应 `WORKDAYS` 常量。
- 调整报告版式：改 `report.py` 的 `render_html`（纯标准库，无外部依赖）。
