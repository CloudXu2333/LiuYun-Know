"""
LLM 配置 API
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import traceback

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import MessageRole
from app.schemas.llm_config import (
    LLMProvider, LLMModelInfo, LLMConfigResponse,
    ChatWithModelRequest, DEFAULT_PROVIDERS, DEFAULT_MODELS,
    UserLLMConfigCreate, UserLLMConfigUpdate, UserLLMConfigResponse
)
from app.schemas.chat import ConversationCreate, ConversationResponse, MessageResponse
from app.services.chat_service import ChatService
from app.services.llm_config_service import LLMConfigService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.ai.llm_manager import llm_manager
from app.ai.agent import conversation_agent

router = APIRouter(prefix="/llm", tags=["LLM配置"])


@router.get("/providers", response_model=List[LLMProvider])
async def get_providers(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有 LLM 提供商列表
    """
    return llm_manager.get_providers()


@router.get("/models", response_model=List[LLMModelInfo])
async def get_models(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    获取模型列表
    
    Args:
        provider: 提供商 ID（可选，不传返回所有模型）
    """
    return llm_manager.get_models(provider)


@router.get("/config", response_model=LLMConfigResponse)
async def get_config(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前 LLM 配置
    """
    return llm_manager.get_config_response()


@router.post("/chat/stream")
async def chat_with_model_stream(
    request: ChatWithModelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    使用指定模型进行流式对话
    
    支持：
    - 选择不同的模型（Claude/GPT/Gemini）
    - 使用自定义 API Key 和 Base URL
    - 关联知识库进行 RAG 对话
    """
    # 获取或创建对话
    conversation = None
    if request.conversation_id:
        conversation = await ChatService.get_conversation(
            db, request.conversation_id, current_user
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
    else:
        conversation = await ChatService.create_conversation(
            db, current_user, ConversationCreate(title="新对话")
        )
        await db.commit()
        await db.refresh(conversation)
    
    # 确定使用的 API 配置
    api_key = request.api_key
    base_url = request.base_url
    model = request.model
    
    # 如果指定了保存的配置 ID，使用保存的配置
    if request.config_id:
        saved_config = await LLMConfigService.get_config(db, request.config_id, current_user)
        if saved_config:
            api_key = saved_config.api_key
            base_url = saved_config.base_url
            model = saved_config.model
            print(f"[LLM Config] Using saved config: {saved_config.name}")
    
    # 调试日志
    print(f"[LLM Config] Provider: {request.provider}, Model: {model}")
    print(f"[LLM Config] Request API Key: {api_key[:10] if api_key else 'None'}...")
    print(f"[LLM Config] Request Base URL: {base_url}")
    
    # DeepSeek 强制使用专用配置（不受前端传入的 base_url 影响）
    if request.provider == "deepseek":
        from app.config import settings
        if not api_key:
            api_key = settings.deepseek_api_key or settings.openai_api_key
        base_url = settings.deepseek_api_base
        print(f"[LLM Config] Using DeepSeek config - API Key: {api_key[:10] if api_key else 'None'}..., Base URL: {base_url}")
    # 其他提供商：如果没有指定 base_url，使用默认配置
    elif request.provider and not base_url:
        for p in DEFAULT_PROVIDERS:
            if p.id == request.provider:
                base_url = p.base_url if p.base_url else None
                break
        print(f"[LLM Config] Using {request.provider} config - Base URL: {base_url}")
    
    async def generate():
        """流式生成器 - 使用 LangGraph Agent"""
        thinking_steps = []  # 收集思考步骤
        web_sources = []
        kb_sources = None
        memory_sources = []  # 收集长时记忆来源
        
        try:
            # 发送对话 ID
            yield f"data: {json.dumps({'conversation_id': str(conversation.id), 'type': 'init'})}\n\n"
            
            # 获取历史消息
            history_messages = await ChatService.get_conversation_messages(db, conversation.id)
            
            # 转换历史消息格式（不再限制数量，由 context_manager 处理）
            history_for_agent = [
                {
                    "role": msg.role.value if hasattr(msg.role, 'value') else msg.role,
                    "content": msg.content
                }
                for msg in history_messages
            ]
            
            # 获取知识库信息
            kb_working_dir = None
            kb_name = None
            if request.knowledge_base_id:
                kb = await KnowledgeBaseService.get_knowledge_base(
                    db, int(request.knowledge_base_id), current_user.id
                )
                if kb:
                    kb_working_dir = kb.working_dir
                    kb_name = kb.name
            
            # 保存用户消息
            user_msg = await ChatService.create_message(
                db=db,
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=request.message,
                model=model
            )
            
            # 使用 LangGraph Agent 流式处理
            full_response = ""
            
            async for event in conversation_agent.run_stream(
                user_query=request.message,
                history_messages=history_for_agent,
                enable_web_search=request.enable_web_search,
                kb_working_dir=kb_working_dir,
                kb_name=kb_name,
                model=model,
                api_key=api_key,
                base_url=base_url,
                system_prompt="你是一个有帮助的AI助手。请用中文回答问题。",
                max_context_tokens=request.max_context_tokens,
                db=db,  # 传入数据库会话
                user_id=current_user.id,  # 传入用户 ID
                memory_top_k=current_user.memory_top_k,  # 用户配置的普通记忆检索数量
                core_memory_threshold=current_user.core_memory_threshold  # 用户配置的核心记忆阈值
            ):
                event_type = event.get("type")
                
                if event_type == "thinking_step":
                    step = event.get("step", "")
                    thinking_steps.append(step)
                    yield f"data: {json.dumps({'type': 'thinking_step', 'step': step})}\n\n"
                
                elif event_type == "search_start":
                    yield f"data: {json.dumps({'type': 'search_start'})}\n\n"
                
                elif event_type == "search_complete":
                    web_sources = event.get("sources", [])
                    yield f"data: {json.dumps({'type': 'search_complete', 'sources': web_sources})}\n\n"
                
                elif event_type == "search_error":
                    yield f"data: {json.dumps({'type': 'search_error', 'error': event.get('error', '')})}\n\n"
                
                elif event_type == "kb_sources":
                    kb_sources = event.get("sources")
                    yield f"data: {json.dumps({'type': 'kb_sources', 'sources': kb_sources})}\n\n"
                
                elif event_type == "memory_sources":
                    # 长时记忆来源事件
                    memory_sources = event.get("memories", [])
                    yield f"data: {json.dumps({'type': 'memory_sources', 'memories': memory_sources})}\n\n"
                
                elif event_type == "context_info":
                    # 发送上下文信息给前端
                    yield f"data: {json.dumps({'type': 'context_info', 'info': event.get('info', {})})}\n\n"
                
                elif event_type == "content":
                    chunk = event.get("content", "")
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
                
                elif event_type == "error":
                    yield f"data: {json.dumps({'error': event.get('error', ''), 'type': 'error'})}\n\n"
                
                elif event_type == "done":
                    # 保存助手回复（包含元数据）
                    msg_metadata = {}
                    if web_sources:
                        msg_metadata['web_sources'] = web_sources
                    if kb_sources:
                        msg_metadata['sources'] = kb_sources
                    if thinking_steps:
                        msg_metadata['thinking_steps'] = thinking_steps
                    if memory_sources:
                        msg_metadata['memory_sources'] = memory_sources
                    
                    assistant_msg = await ChatService.create_message(
                        db=db,
                        conversation_id=conversation.id,
                        role=MessageRole.ASSISTANT,
                        content=full_response,
                        model=model,
                        metadata=msg_metadata if msg_metadata else None
                    )
                    
                    # 发送完成信号
                    done_data = {'type': 'done', 'model': model}
                    if kb_sources:
                        done_data['sources'] = kb_sources
                    yield f"data: {json.dumps(done_data)}\n\n"
                    yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = str(e)
            print(f"[Chat Stream] Error: {error_msg}")
            traceback.print_exc()
            yield f"data: {json.dumps({'error': error_msg, 'type': 'error'})}\n\n"
        finally:
            try:
                await db.commit()
            except Exception as commit_error:
                print(f"[Chat Stream] Commit error: {commit_error}")
                await db.rollback()
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/test")
async def test_llm_connection(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    测试 LLM 连接
    
    Args:
        provider: 提供商 ID
        model: 模型名称
        api_key: API Key（可选）
        base_url: Base URL（可选）
    """
    # 确定 base_url 和 api_key
    # DeepSeek 强制使用专用配置
    if provider == "deepseek":
        from app.config import settings
        if not api_key:
            api_key = settings.deepseek_api_key or settings.openai_api_key
        base_url = settings.deepseek_api_base
    elif not base_url:
        # 其他提供商：如果没有指定 base_url，使用默认配置
        for p in DEFAULT_PROVIDERS:
            if p.id == provider:
                base_url = p.base_url if p.base_url else None
                break
    
    try:
        messages = [{"role": "user", "content": "请用一句话介绍你自己。"}]
        response = await llm_manager.chat_completion(
            messages=messages,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=100,
        )
        
        content = response.choices[0].message.content
        return {
            "success": True,
            "message": "连接成功",
            "response": content,
            "model": model,
            "provider": provider
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
            "model": model,
            "provider": provider
        }


# ============ 用户配置管理 ============

@router.post("/configs", response_model=UserLLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_user_config(
    config_data: UserLLMConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建用户 LLM 配置"""
    config = await LLMConfigService.create_config(db, current_user, config_data)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/configs", response_model=List[UserLLMConfigResponse])
async def get_user_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的所有 LLM 配置"""
    configs = await LLMConfigService.get_user_configs(db, current_user)
    return configs


@router.get("/configs/{config_id}", response_model=UserLLMConfigResponse)
async def get_user_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个配置"""
    config = await LLMConfigService.get_config(db, config_id, current_user)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    return config


@router.put("/configs/{config_id}", response_model=UserLLMConfigResponse)
async def update_user_config(
    config_id: str,
    config_data: UserLLMConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新配置"""
    config = await LLMConfigService.get_config(db, config_id, current_user)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    updated_config = await LLMConfigService.update_config(db, config, config_data)
    await db.commit()
    await db.refresh(updated_config)
    return updated_config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除配置"""
    config = await LLMConfigService.get_config(db, config_id, current_user)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    await LLMConfigService.delete_config(db, config)
    await db.commit()
    return None
