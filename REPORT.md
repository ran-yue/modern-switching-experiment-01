# 实验一报告

姓名：尹俊杰  学号：2024280377  GitHub：ran-yue  提交编号：填写

## 实验目的
本实验旨在通过 Python 命令行仿真，对比研究“固定时隙电路交换”与“共享 FIFO 分组交换”在资源分配方式上的核心差异[span_1](start_span)[span_1](end_span)。重点考察固定时隙预留与共享 FIFO 队列在资源利用、统计复用收益、包头开销以及排队时延等维度的表现，深入理解不同交换机制在各类业务场景下的性能特征与局限性[span_2](start_span)[span_2](end_span)。

## 原理和模型
- **固定时隙预留**：电路交换在连接建立后，周期性地为用户预留固定时隙（当前服务用户 `tick % users`），其他用户在时隙空闲时也无法借用，未填满的时隙造成带宽浪费[span_3](start_span)[span_3](end_span)。
- **统计复用**：分组交换采用共享 FIFO 队列，按需动态分配线路带宽，突发流量可以共享全部链路容量，显著提高了资源的动态利用率[span_4](start_span)[span_4](end_span)。
- **包头**：分组交换每条记录带有固定长度的包头（32 bit），虽然实现了灵活寻址，但在连续满载或小分组场景下会引入额外的线路传输开销[span_5](start_span)[span_5](end_span)。
- **FIFO**：分组交换采用先入先出队列，严格保证顺序，大记录可跨 tick 续传，但不允许分组交错[span_6](start_span)[span_6](end_span)。
- **缓存准入**：记录到达时若“已预留 payload + 本条 payload”超过总缓存配额，则整条尾丢弃；完整交付后才释放配额[span_7](start_span)[span_7](end_span)。
- **有限观察窗口**：仿真在固定 `[0, 256)` ticks 窗口内停止，不进行额外的排空处理，未完成记录全部计入窗口结束时的积压（`backlog`）[span_8](start_span)[span_8](end_span)。
- **抽象链路与 PCM 示例的区别**：本实验采用简化的单链路抽象速率（128 kbit/s），不涉及真实的物理传播、误码重传或多跳路由；而标准的 PCM（脉冲编码调制）多路复用采用 32 时隙 × 8 bit × 8000 帧/s = 2.048 Mbit/s 的固定结构，两者的复用粒度和信令开销模型存在本质不同[span_9](start_span)[span_9](end_span)。

## 手工推演
- **小例子设定**：设 2 用户、2 tick、每 tick 1 ms、链路容量 128 bit、包头 32 bit。在 tick 0 时，用户 1 到达一条 96 bit 的记录[span_10](start_span)[span_10](end_span)。
- **电路交换推演**：tick 0 属于用户 0（闲置），tick 1 属于用户 1 并开始发送 96 bit（加包头或在容量内传输），于 2 ms 边界完成交付[span_11](start_span)[span_11](end_span)。
- **分组交换推演**：tick 0 共享 FIFO 收到该记录（初始 wire 长度 96 + 32 = 128 bit），在 tick 0 内一次性发送完毕并于 1 ms 边界交付[span_12](start_span)[span_12](end_span)。
- **结论**：两者的有效载荷利用率均为 37.5%（96/256 bit），但电路交换的线路忙碌率为 37.5%，分组交换为 50%，且分组交换的平均时延（1 ms）优于电路交换（2 ms），验证了“相同有效利用率下时延与开销并不相同[span_13](start_span)”[span_13](end_span)。

## 实验结果
![指标比较](results/comparison_metrics.png)
![队列占用](results/queue_occupancy.png)
![PCM示例](results/pcm_frame_view.png)

列出四种业务的有效载荷利用率、时延、丢失与积压，解释至少一个“利用率和时延指向不同结论”的例子。

## 自拟反例
- **测试文件**：`student_tests/test_my_case.py` 中的 `test_packet_left_in_queue_is_not_completed`[span_16](start_span)[span_16](end_span)。
- **输入与预期**：设容量 64 bit，队列中有一条 128 bit payload（总 wire 160 bit）的记录。在 tick 0 发送 64 bit 后，剩余 96 bit 留在队列中[span_17](start_span)[span_17](end_span)。
- **断言与揭示的错误**：断言 `wire_bits == 64`、`completed == []` 且队列长度保持为 1。该反例成功揭示并防止了“将仿真结束时仍未发送完成的半截数据错误计入已完成交付列表”的实现缺陷[span_18](start_span)[span_18](end_span)。

## 分析与限制

- **统计复用的优势**：当业务具有明显的突发性（如间歇性数据传输）时，统计复用允许用户动态共享全部带宽，避免了电路交换中固定时隙闲置造成的资源浪费[span_19](start_span)[span_19](end_span)。
- **满载连续场景分组未必更好的原因**：在连续满载场景下，分组交换每条记录都需要额外传输 32 bit 包头，这部分开销占用了宝贵的线路容量，导致其有效载荷利用率可能逊色于无需包头的纯电路预留[span_20](start_span)[span_20](end_span)。
- **未完成数据与丢包的区别**：未完成数据（`backlog`）是由于观察窗口有限或排队未发完而留在队列中的数据，它们并非由于缓存溢出被主动丢弃（`dropped`），不能直接当成丢包处理[span_21](start_span)[span_21](end_span)。
- **为何不能只看成功记录的平均时延**：如果系统中有大量数据因超时或积压未完成，仅统计极少数成功交付记录的平均时延，会严重低估系统的实际排队拥塞程度[span_22](start_span)[span_22](end_span)。

## AI使用说明

- **关联文件**：见 `AI_LOG_TEMPLATE.md`[span_23](start_span)[span_23](end_span)。
- **核心循环与验证决策**：在实现 `serve_packet` 时，AI 协助梳理了跨 tick 续传时 `remaining_wire_bits` 的扣减逻辑。通过编写针对性的边界单元测试（如预算不足时的部分发送验证），确保了每次扣减准确无误，且未重复计算包头[span_24](start_span)[span_24](end_span)。

## 参考资料

- 课程实验指导书与 `README.md` / `docs/model_contract.md`[span_25](start_span)[span_25](end_span)。
- Python `pytest` 官方文档与现代交换原理课堂讲义[span_26](start_span)[span_26](end_span)。
