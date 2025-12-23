"""
ChatService 联网搜索集成测试
Property 1: Search Toggle Behavior
"""
import sys
import os

# 添加 backend 目录到 Python 路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.schemas.web_search import SearchResult


class TestSearchToggleBehavior:
    """Property 1: Search Toggle Behavior - 测试搜索开关行为"""

    def test_chat_request_has_enable_web_search_field(self):
        """ChatRequest 应该有 enable_web_search 字段"""
        from app.schemas.chat import ChatRequest
        
        # 默认值应该是 False
        request = ChatRequest(message="test")
        assert request.enable_web_search is False
        
        # 可以设置为 True
        request = ChatRequest(message="test", enable_web_search=True)
        assert request.enable_web_search is True

    @pytest.mark.asyncio
    async def test_web_search_called_when_enabled(self):
        """当 enable_web_search=True 时应该调用 WebSearchService"""
        from app.services.chat_service import ChatService
        
        with patch("app.services.chat_service.web_search_service") as mock_search_service:
            mock_search_service.enabled = True
            mock_search_service.search = AsyncMock(return_value=Mock(
                results=[
                    SearchResult(url="https://example.com", title="Test", snippet="Content", source="tavily")
                ]
            ))
            mock_search_service._select_top_results = Mock(return_value=[
                SearchResult(url="https://example.com", title="Test", snippet="Content", source="tavily")
            ])
            mock_search_service.format_context = Mock(return_value="【联网搜索结果】\n...")
            
            with patch("app.services.chat_service.llm_client") as mock_llm:
                mock_llm.count_tokens = Mock(return_value=10)
                mock_llm.chat_completion = AsyncMock(return_value=Mock(
                    choices=[Mock(message=Mock(content="AI response"))],
                    usage=Mock(completion_tokens=20),
                    model="test-model"
                ))
                
                # Mock 数据库操作
                mock_db = AsyncMock()
                mock_conversation = Mock(id="test-id", title="Test")
                
                with patch.object(ChatService, "get_conversation_messages", return_value=[]):
                    with patch.object(ChatService, "create_message", return_value=Mock()):
                        # 调用 chat_with_llm，启用联网搜索
                        await ChatService.chat_with_llm(
                            db=mock_db,
                            conversation=mock_conversation,
                            user_message="test query",
                            stream=False,
                            enable_web_search=True
                        )
                        
                        # 验证搜索服务被调用
                        mock_search_service.search.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_web_search_not_called_when_disabled(self):
        """当 enable_web_search=False 时不应该调用 WebSearchService"""
        from app.services.chat_service import ChatService
        
        with patch("app.services.chat_service.web_search_service") as mock_search_service:
            mock_search_service.enabled = True
            mock_search_service.search = AsyncMock()
            
            with patch("app.services.chat_service.llm_client") as mock_llm:
                mock_llm.count_tokens = Mock(return_value=10)
                mock_llm.chat_completion = AsyncMock(return_value=Mock(
                    choices=[Mock(message=Mock(content="AI response"))],
                    usage=Mock(completion_tokens=20),
                    model="test-model"
                ))
                
                mock_db = AsyncMock()
                mock_conversation = Mock(id="test-id", title="Test")
                
                with patch.object(ChatService, "get_conversation_messages", return_value=[]):
                    with patch.object(ChatService, "create_message", return_value=Mock()):
                        # 调用 chat_with_llm，禁用联网搜索
                        await ChatService.chat_with_llm(
                            db=mock_db,
                            conversation=mock_conversation,
                            user_message="test query",
                            stream=False,
                            enable_web_search=False
                        )
                        
                        # 验证搜索服务未被调用
                        mock_search_service.search.assert_not_called()


class TestSystemPromptBuilding:
    """测试系统提示词构建"""

    def test_build_system_prompt_without_search(self):
        """没有搜索上下文时应该返回基础提示词"""
        from app.services.chat_service import ChatService
        
        base_prompt = "你是一个有帮助的 AI 助手。"
        result = ChatService._build_system_prompt(base_prompt, None)
        assert result == base_prompt

    def test_build_system_prompt_with_search(self):
        """有搜索上下文时应该合并到提示词中"""
        from app.services.chat_service import ChatService
        
        base_prompt = "你是一个有帮助的 AI 助手。"
        search_context = "【联网搜索结果】\n[来源1] Test\nURL: https://example.com\n内容: Content"
        
        result = ChatService._build_system_prompt(base_prompt, search_context)
        
        assert base_prompt in result
        assert search_context in result
        assert "【联网搜索结果】" in result
