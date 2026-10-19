from collections import deque
from src.models import Config, Pending
from src.part2_packet import serve_packet


def test_packet_left_in_queue_is_not_completed():
    """
    自拟反例：仿真结束时仍未发送完成的数据包（因预算耗尽留在队列中），
    绝不应该被计入已完成发送的列表。

    手算预期：
    - 设 slot_bits = 64（本 tick 链路容量只有 64 bit）。
    - 队列中有一条记录：payload = 128 bit，remaining_wire_bits = 128 + 32 = 160 bit（含 32 bit 包头）。
    - 在 tick 0 调用 serve_packet：
      1. 实际只能发送 64 bit，剩余 160 - 64 = 96 bit 留在队列中跨 tick 续传。
      2. 本 tick 实际发送 wire_bits = 64。
      3. 因为没有完全发完，完成列表 completed 必须为空（[]），队列中仍然保留该未完成记录。
      4. 验证程序没有把“留在队列中的半截数据”错误地算作已完成发送。
    """
    # 1. 构造配置与队列
    cfg = Config(
        users=4,
        ticks=10,
        slot_bits=64,  # 容量设为 64 bit，小于数据包总大小 160 bit
        tick_ms=1,
        header_bits=32,
        buffer_payload_bits=4096,
    )

    # 构造一个 128 bit payload 的记录，初始化 wire 长度为 128 + 32 = 160
    uncompleted_pending = Pending(
        user=0,
        arrival_tick=0,
        payload_bits=128,
        remaining_wire_bits=160
    )
    queue = deque([uncompleted_pending])

    # 2. 调用函数
    wire_bits, completed = serve_packet(queue, tick=0, cfg=cfg)

    # 3. 编写严密的断言进行验证
    assert wire_bits == 64, "预算 64 bit 应当被全部耗尽用于发送"
    assert len(completed) == 0, "数据包未完全发送，绝对不能计入已完成交付列表"
    assert len(queue) == 1, "未完成的数据包应当留在队列中等待下一 tick 续传"
    assert queue[0].remaining_wire_bits == 96, "剩余未发送的 wire 长度应正确扣减为 96 bit (160 - 64)"
