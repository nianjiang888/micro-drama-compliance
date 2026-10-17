# -*- coding: utf-8 -*-
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from checker import new_case, run, to_html_report

c = new_case()
c.update({
    "title": "重生后我把霸总扫地出门", "producer": "星野文化传媒工作室", "province": "广东省",
    "episodes": 80, "minutes_per_episode": 2.0,
    "investment": 280000, "subjects": ["都市", "重生", "霸总"],
    "subject_desc": "女主重生复仇，逆袭打脸豪门总裁",
    "has_production_license": False,
    "uses_ai": True, "ai_scope": "AI 生成场景、AI 配音、部分镜头 AI 换脸",
    "target_launch": "2026-09-20", "shooting_days": 5, "post_days": 10,
})
r = run(c)
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample-report.html")
p = to_html_report(r, out)
print("saved:", p, os.path.getsize(p), "bytes")
