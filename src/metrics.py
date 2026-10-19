"""任务3：补全指标统计。"""
def summarize(raw, cfg):
    """返回字典，键名必须保留：
    payload_utilization=delivered_payload_bits/(cfg.ticks*cfg.slot_bits)
    wire_utilization=wire_sent_bits/(cfg.ticks*cfg.slot_bits)
    mean_delay_ms、max_delay_ms：完成记录的delay_ticks乘cfg.tick_ms；
      无完成记录时两者返回None，不能写0掩盖无送达。
    loss_ratio=dropped_payload_bits/generated_payload_bits；无生成数据时为0。
    backlog_payload_bits：所有未完成记录的原始payload总和，直接取raw对应值。
    只用观察窗口[0,ticks)，不追加排空时间；有效载荷按完整交付记录计数。
    raw['completed']元素含payload_bits、delay_ticks、user。
    要检查generated=delivered+dropped+backlog，不相等抛ValueError。
    """
    generated = raw["generated_payload_bits"]
    delivered = raw["delivered_payload_bits"]
    dropped = raw["dropped_payload_bits"]
    backlog = raw["backlog_payload_bits"]
    wire_sent = raw["wire_sent_bits"]
    completed = raw["completed"]

    # 守恒检查：生成 payload 不等于 交付 + 丢弃 + 积压 时抛出 ValueError
    if generated != delivered + dropped + backlog:
        raise ValueError(
            f"Payload conservation violated: {generated} != {delivered} + {dropped} + {backlog}"
        )

    total_capacity = cfg.ticks * cfg.slot_bits
    payload_utilization = delivered / total_capacity
    wire_utilization = wire_sent / total_capacity

    if not completed:
        mean_delay_ms = None
        max_delay_ms = None
    else:
        delays = [
            (item["delay_ticks"] if isinstance(item, dict) else item.delay_ticks)
            for item in completed
        ]
        mean_delay_ms = (sum(delays) / len(delays)) * cfg.tick_ms
        max_delay_ms = max(delays) * cfg.tick_ms

    if generated == 0:
        loss_ratio = 0.0
    else:
        loss_ratio = dropped / generated

    return {
        "payload_utilization": payload_utilization,
        "wire_utilization": wire_utilization,
        "mean_delay_ms": mean_delay_ms,
        "max_delay_ms": max_delay_ms,
        "loss_ratio": loss_ratio,
        "backlog_payload_bits": backlog,
    }

