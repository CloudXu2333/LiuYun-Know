# LangGraph 重构说明

## 重构内容

将 `agent.py` 的流式实现改为完全基于 LangGraph，为后续接入 MCP 工具调用做准备。

## 主要改动

### 1. 状态定义增强
```python
class AgentState(TypedDict):
    # ... 原有字段
    # 新增字段
    max_context_tokens: int
    db: Any
    user_id: Optional[str]
    memory_top_k: int
    core_memory_threshold: int
    stream_queue: Optional[asyncio.Queue]  # 关键：用于流式输出
```

### 2. 节点支持流式输出
所有节点（`_analyze_node`、`_web_search_node`、`_kb_query_node`、`_generate_node`）都通过 `stream_queue` 实时发送事件：
- 思考步骤
- 搜索结果
- 知识库来源
- LLM token 流式输出

### 3. run_stream 方法重构
- 使用 `asyncio.Queue` 在图执行和外部调用之间传递事件
- 图在后台异步执行（`asyncio.create_task`）
- 主函数从队列读取事件并 yield 给调用方
- 实现了真正的 token 级流式输出

## 架构优势

### 当前优势
1. **统一流程管理**：所有逻辑都在 LangGraph 图中
2. **状态可追踪**：每个节点的状态变化都清晰可见
3. **易于调试**：可以单独测试每个节点

### 为 MCP 做准备
1. **工具调用循环**：可以轻松添加 `tools` 节点和循环边
2. **条件路由**：LLM 决定是否继续调用工具
3. **状态持久化**：工具调用结果自动保存在状态中

## 后续 MCP 接入示例

```python
# 1. 添加工具节点
workflow.add_node("mcp_tools", mcp_tool_node)

# 2. 在 generate 节点前添加工具调用决策
workflow.add_conditional_edges(
    "kb_query",
    should_call_tools,  # LLM 决定是否需要调用工具
    {
        "call_tools": "mcp_tools",
        "generate": "generate"
    }
)

# 3. 工具执行后可以循环或生成
workflow.add_conditional_edges(
    "mcp_tools",
    should_continue_tools,
    {
        "continue": "mcp_tools",  # 继续调用工具
        "generate": "generate"    # 生成最终回复
    }
)
```

## 流式输出机制

```
┌─────────────────┐
│  run_stream()   │
│  (主函数)        │
└────────┬────────┘
         │
         │ 创建 stream_queue
         │ 启动 graph_task
         │
         ▼
┌─────────────────────────┐
│  graph.ainvoke()        │
│  (后台异步执行)          │
│                         │
│  ┌─────────────────┐   │
│  │ analyze_node    │───┼──► queue.put(event)
│  └─────────────────┘   │
│  ┌─────────────────┐   │
│  │ web_search_node │───┼──► queue.put(event)
│  └─────────────────┘   │
│  ┌─────────────────┐   │
│  │ kb_query_node   │───┼──► queue.put(event)
│  └─────────────────┘   │
│  ┌─────────────────┐   │
│  │ generate_node   │───┼──► queue.put(chunk) (逐token)
│  └─────────────────┘   │
└─────────────────────────┘
         │
         │ queue.put(None)  # 结束标记
         │
         ▼
┌─────────────────┐
│  while True:    │
│    event = await│
│    queue.get()  │
│    yield event  │
└─────────────────┘
```

## 兼容性

- ✅ 保持了原有的 API 接口不变
- ✅ 所有事件类型与之前一致
- ✅ 前端无需修改
- ✅ 非流式 `run` 方法仍然可用

## 测试建议

1. 测试基本对话（无搜索、无知识库）
2. 测试联网搜索
3. 测试知识库查询
4. 测试长期记忆加载
5. 测试流式输出的实时性
