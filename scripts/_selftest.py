# -*- coding: utf-8 -*-
"""内部自测脚本，验证三种典型场景的判定结果。打包前删除。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from checker import new_case, run, to_report

print("\n\n############ 案例一：AI制作低成本都市剧（预期三类） ############\n")
c1 = new_case()
c1.update({
    "title": "重生后我把霸总扫地出门", "producer": "某文化传媒工作室", "province": "广东省",
    "episodes": 80, "minutes_per_episode": 2.0,
    "investment": 280000, "subjects": ["都市", "重生", "霸总"],
    "subject_desc": "女主重生复仇，逆袭打脸豪门总裁",
    "has_production_license": False,
    "uses_ai": True, "ai_scope": "AI生成场景、AI配音、部分AI换脸",
    "target_launch": "2026-09-20", "shooting_days": 5, "post_days": 10,
})
r1 = run(c1)
print(to_report(r1))

print("\n\n############ 案例二：扫黑刑侦题材（预期一类，题材触发） ############\n")
c2 = new_case()
c2.update({
    "title": "利刃出鞘", "producer": "某影视传媒有限公司", "province": "浙江省",
    "episodes": 60, "minutes_per_episode": 8.0,
    "investment": 800000,
    "subjects": ["刑侦", "扫黑"],
    "subject_desc": "基层公安干警侦破跨省涉黑案件，涉及公安办案流程与司法程序",
    "has_production_license": True,
    "uses_ai": False,
    "target_launch": "2026-11-15", "shooting_days": 25, "post_days": 30,
})
r2 = run(c2)
print(to_report(r2))

print("\n\n############ 案例三：临界投资额 + 无资质 + 工期赶不上（预期二类，多重告警） ############\n")
c3 = new_case()
c3.update({
    "title": "长夜将明", "producer": "个人工作室", "province": "江苏省",
    "episodes": 100, "minutes_per_episode": 3.0,
    "investment": 1150000,
    "subjects": ["古装", "权谋"],
    "subject_desc": "架空王朝夺嫡，权谋斗争",
    "has_production_license": False, "partner_licensed": False,
    "uses_ai": False,
    "target_launch": "2026-10-01", "shooting_days": 20, "post_days": 25,
})
r3 = run(c3)
print(to_report(r3))

print("\n\n############ 案例四：单集25分钟（预期不适用本办法） ############\n")
c4 = new_case()
c4.update({
    "title": "山海旧事", "producer": "某网络科技公司", "province": "北京市",
    "episodes": 24, "minutes_per_episode": 25.0,
    "investment": 5000000, "subjects": ["奇幻"],
    "subject_desc": "少年寻宝冒险",
    "has_production_license": True, "uses_ai": False,
    "target_launch": "2027-01-01",
})
r4 = run(c4)
print(to_report(r4))
