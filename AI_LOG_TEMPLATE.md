# AI协作记录 (AI_LOG.md)

工具与模型：使用 AI 助手辅助梳理模型边界与边界条件处理。

## 一项真实协作过程

- **需求与输入**：在实现 `src/part2_packet.py` 中的 `serve_packet` 函数时，需要处理共享 FIFO 队列的跨 tick 续传与预算扣减，同时确保框架已初始化的包头不被重复计算。
- **AI建议**：AI 建议采用 `while` 循环结合 `min(budget, head.remaining_wire_bits)` 实时扣减预算，并明确提示 `remaining_wire_bits` 在入队时已包含包头，函数体内无需再次累加。
- **我的手算与测试**：
  - **输入**：编写了自定义反例测试 `test_packet_left_in_queue_is_not_completed`（见 `student_tests/test_my_case.py`），设定容量 64 bit，队列中有一条总 wire 长度 160 bit（含 32 bit 包头）的记录。
  - **预期**：tick 0 发送 64 bit 预算耗尽，剩余 96 bit 留在队列中，`completed` 列表为空。
  - **实际运行**：执行 `pytest student_tests -q`，输出 `1 passed`，与手算预期完全一致。
- **修正或采纳理由**：采纳了 AI 关于“不重复加包头”和“部分发送不计入完成”的逻辑建议。结合实验模型契约（Model Contract），通过编写独立的边界测试进行了严密的用例验证，确保代码符合守恒和状态不变量。
- **我能解释的核心逻辑**：
  - **避免重复加包头**：因为框架在数据包入队时已经统一完成了 `payload_bits + header_bits` 的初始化，发送函数只负责在线路上消耗 `remaining_wire_bits`，因此绝不能在循环中二次叠加 `header_bits`。
  - **避免借用固定时隙**：在电路交换中通过 `tick % cfg.users` 严格锁定当前服务用户，空闲时直接返回 0，杜绝了跨用户时隙借用。
  - **防止统计遗漏积压**：在指标统计（`summarize`）中，严格通过守恒式 `generated == delivered + dropped + backlog` 进行 `ValueError` 校验，未完成记录的原始 payload 统一计入 `backlog`，不以 0 时延掩盖未送达样本。
