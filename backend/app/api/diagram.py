"""
流程图生成 API - AI 流程图生成

调用流程：
1. LLM 分析用户需求，决定调用 create_diagram 工具
2. 后端直接调用 DiagramService 生成 Draw.io XML
3. 前端渲染流程图
"""
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.ai.llm_manager import llm_manager
from app.services.diagram_service import diagram_service

router = APIRouter(prefix="/diagram", tags=["流程图"])


class DiagramRequest(BaseModel):
    description: str
    conversation_history: list = []
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    config_id: Optional[str] = None  # 用户配置 ID
    platform_config_id: Optional[str] = None  # 平台配置 ID


DIAGRAM_SYSTEM_PROMPT = """你是一个专业的流程图设计助手。你可以使用 create_diagram 工具来创建流程图。

当用户描述他们想要的流程图时，你需要：
1. 理解用户的需求
2. 设计合理的流程结构
3. 调用 create_diagram 工具生成流程图

## 设计规范

### 形状选择
- ellipse: 椭圆 - 用于开始/结束节点
- rectangle: 矩形 - 用于普通处理步骤
- rhombus: 菱形 - 用于判断/条件分支
- parallelogram: 平行四边形 - 用于输入/输出
- cylinder: 圆柱体 - 用于数据库操作
- cloud: 云形状 - 用于外部系统/服务
- document: 文档形状 - 用于文档/报告

### 颜色规范
- 开始/结束: fillColor=#d5e8d4, strokeColor=#82b366 (绿色)
- 普通步骤: fillColor=#dae8fc, strokeColor=#6c8ebf (蓝色)
- 判断条件: fillColor=#fff2cc, strokeColor=#d6b656 (黄色)
- 输入输出: fillColor=#f8cecc, strokeColor=#b85450 (红色)
- 数据库: fillColor=#e1d5e7, strokeColor=#9673a6 (紫色)
- 外部系统: fillColor=#f5f5f5, strokeColor=#666666 (灰色)

### 布局规范（重要！避免线条交叉）
- 主流程居中: x=400
- 垂直起始: y=80
- 垂直间距: 至少 120px（避免节点太近）
- 分支偏移: 左分支 x=150，右分支 x=650（间距要大，避免线条交叉）
- 如果有多个分支，每个分支水平间距至少 200px
- 节点尺寸: width=140, height=60（菱形用 width=160, height=80）
- 汇合节点要放在所有分支的正下方中间位置

### 布局示例
```
主流程（单列）:
  开始 (400, 80)
    ↓
  步骤1 (400, 200)
    ↓
  步骤2 (400, 320)
    ↓
  结束 (400, 440)

带分支的流程:
  开始 (400, 80)
    ↓
  判断 (400, 200)
   ↙     ↘
是分支    否分支
(150,320) (650,320)
   ↘     ↙
  汇合节点 (400, 440)
    ↓
  结束 (400, 560)
```

### 连接线规范
- 从上到下的正常流程不需要 label
- 判断分支必须标注 "是"/"否" 或 "成功"/"失败"
- 分支线从菱形的左右两侧出发（不要从底部）
- 汇合线从分支节点底部出发，进入汇合节点顶部

请根据用户的描述，设计并生成流程图。如果用户要求修改，请基于之前的设计进行调整。
"""


@router.post("/generate-stream")
async def generate_diagram_stream(
    request: DiagramRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    流式生成流程图（MCP 工具调用模式）
    
    AI 会自动决定是否需要调用 create_diagram 工具
    """
    async def generate():
        try:
            # Step 1: 分析需求
            yield f"data: {json.dumps({'type': 'step', 'step': 1, 'title': '分析需求', 'content': '正在理解您的流程描述...'})}\n\n"
            
            # 构建消息
            messages = [{"role": "system", "content": DIAGRAM_SYSTEM_PROMPT}]
            
            # 添加对话历史
            for msg in request.conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # 添加当前请求
            messages.append({"role": "user", "content": request.description})
            
            # Step 2: AI 思考并决定是否调用工具
            yield f"data: {json.dumps({'type': 'step', 'step': 2, 'title': 'AI 分析', 'content': '正在设计流程图结构...'})}\n\n"
            
            # 获取工具定义
            tools = diagram_service.get_tools()
            
            # 确定使用的 API 配置
            from app.config import settings
            from app.services.llm_config_service import LLMConfigService, PlatformLLMConfigService
            
            use_api_key = None
            use_base_url = None
            model = None
            
            # 优先使用平台配置
            if request.platform_config_id:
                platform_config = await PlatformLLMConfigService.get_config(db, request.platform_config_id)
                if platform_config and platform_config.is_active:
                    use_api_key = platform_config.api_key
                    use_base_url = platform_config.base_url
                    model = platform_config.model
                    print(f"[Diagram] Using platform config: {platform_config.name}")
            # 其次使用用户配置
            elif request.config_id:
                user_config = await LLMConfigService.get_config(db, request.config_id, current_user)
                if user_config:
                    use_api_key = user_config.api_key
                    use_base_url = user_config.base_url
                    model = user_config.model
                    print(f"[Diagram] Using user config: {user_config.name}")
            # 最后使用请求中的配置
            elif request.api_key:
                use_api_key = request.api_key
                use_base_url = request.base_url
                model = request.model
            
            # 如果还没有配置，使用默认配置
            if not use_api_key:
                use_api_key = settings.deepseek_api_key or settings.openai_api_key
                use_base_url = settings.deepseek_api_base or settings.openai_api_base
                model = "deepseek-chat" if settings.deepseek_api_key else settings.default_model
            
            # 创建客户端
            client = llm_manager.get_client(use_api_key, use_base_url)
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message
            
            # 检查是否有工具调用
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    if tool_call.function.name == "create_diagram":
                        yield f"data: {json.dumps({'type': 'step', 'step': 3, 'title': '工具调用', 'content': 'LLM 决定调用 create_diagram 工具...'})}\n\n"
                        
                        # 解析参数
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            yield f"data: {json.dumps({'type': 'error', 'content': '工具参数解析失败'})}\n\n"
                            return
                        
                        # 发送节点信息
                        nodes = arguments.get("nodes", [])
                        edges = arguments.get("edges", [])
                        
                        for node in nodes:
                            node_info = f"节点: {node.get('label', node.get('id', ''))}"
                            yield f"data: {json.dumps({'type': 'node', 'info': node_info})}\n\n"
                        
                        for edge in edges:
                            label = edge.get('label', '')
                            edge_info = f"{edge.get('from', '')} → {edge.get('to', '')}"
                            if label:
                                edge_info += f" ({label})"
                            yield f"data: {json.dumps({'type': 'edge', 'info': edge_info})}\n\n"
                        
                        # 调用流程图服务
                        yield f"data: {json.dumps({'type': 'step', 'step': 4, 'title': '生成流程图', 'content': '正在生成 Draw.io XML...'})}\n\n"
                        
                        result = diagram_service.call_tool(
                            "create_diagram",
                            arguments
                        )
                        
                        if result.get("success"):
                            # 生成 AI 的解释文本
                            title = result.get("title", "流程图")
                            nodes_count = result.get("nodes_count", 0)
                            edges_count = result.get("edges_count", 0)
                            
                            ai_response = f"我已经为您生成了「{title}」流程图，包含 {nodes_count} 个节点和 {edges_count} 条连接。您可以继续描述修改需求，比如：\n- 添加新的步骤\n- 修改节点颜色或形状\n- 调整流程分支"
                            
                            yield f"data: {json.dumps({'type': 'complete', 'xml': result['xml'], 'nodes': nodes, 'edges': edges, 'title': title, 'ai_response': ai_response})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'error', 'content': result.get('error', '生成失败')})}\n\n"
            else:
                # AI 没有调用工具，直接返回文本回复
                content = assistant_message.content or "我理解了您的需求，但需要更多信息来生成流程图。请描述具体的流程步骤。"
                yield f"data: {json.dumps({'type': 'message', 'content': content})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/tool/create")
async def call_create_diagram_tool(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    直接调用 create_diagram 工具
    
    用于前端直接调用工具（不经过 AI）
    """
    result = diagram_service.call_tool("create_diagram", data)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "生成失败"))
    return result


@router.get("/tools")
async def list_diagram_tools(
    current_user: User = Depends(get_current_user)
):
    """
    获取可用的流程图工具列表
    """
    return {
        "tools": diagram_service.get_tools(),
        "description": "流程图生成工具，支持通过 AI 对话或直接调用"
    }
