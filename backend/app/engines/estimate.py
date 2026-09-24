"""对外试算入口：净面积 + 升数的组合计算。

数值口径委托 engines.assembly（同一套组装），本模块仅保留历史函数名，
供引擎测例与种子脚本调用。
"""
from app.engines.assembly import assemble


def estimate_room(length, width, height, openings, coverage, coats):
    return assemble(length, width, height, openings, coverage, coats)
