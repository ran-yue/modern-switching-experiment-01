"""任务2：补全共享FIFO分组交换发送。"""
def serve_packet(queue, tick, cfg):
    """queue为共享deque[Pending]，原地更新。
    remaining_wire_bits已由框架初始化为payload_bits+header_bits，不再重复加包头。
    每tick发送不超过slot_bits；必须发完队首再处理下一项。
    分组允许跨tick续传，但不得与其他分组交错，不能因大于一个时隙就丢弃。
    返回(线速发送比特数,完整发送的Pending列表)；空队列返回(0,[])。
    """
    if not queue:
        return 0, []

    budget = cfg.slot_bits
    wire_bits = 0
    completed_records = []

    while queue and budget > 0:
        head = queue[0]
        sent = min(budget, head.remaining_wire_bits)

        head.remaining_wire_bits -= sent
        wire_bits += sent
        budget -= sent

        if head.remaining_wire_bits == 0:
            completed_records.append(queue.popleft())

    return wire_bits, completed_records

