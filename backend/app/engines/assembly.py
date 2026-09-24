"""试算组装单元（纯计算，不写库）。

把净面积与升数的组装从服务入口拆出，可脱离数据库单独调用：
给定房间几何尺寸/洞口与施工参数，直接得到完整试算结果。

本单元只负责"组装"：净面积公式仍取 wall_area、升数公式仍取
paint_volume，数值口径与 estimate_room 完全一致，不做任何舍入口径
之外的二次加工。
"""
from app.engines.paint_volume import paint_liters
from app.engines.wall_area import wall_area

# 快照中钉选的关键字段：必须与回包字段同源、同值。
SNAPSHOT_FIELDS = ("net_m2", "openings_m2", "liters")


def assemble(length, width, height, openings, coverage, coats):
    """组装一次试算：先算墙面净面积，再据净面积算升数。

    返回完整回包：
      gross_m2/openings_m2/net_m2（面积）、liters/coats/coverage（升数）。
    纯函数，不触碰数据库。
    """
    area = wall_area(length, width, height, openings)
    vol = paint_liters(area["net_m2"], coverage, coats)
    return {**area, **vol}


def build_snapshot(result):
    """从试算结果中钉选需要写入 calc_runs 的净面积、扣除面积与升数。

    快照值直接取自组装回包（同一对象），杜绝写库值与回包值漂移。
    """
    return {k: result[k] for k in SNAPSHOT_FIELDS}
