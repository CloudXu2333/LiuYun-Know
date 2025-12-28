"""
MCP 服务层
负责管理 MCP Server 进程、通信和工具调用
"""
import asyncio
import json
import uuid
import subprocess
import sys
import os
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor


@dataclass
class MCPConnection:
    """MCP 连接信息"""
    process: subprocess.Popen
    tools: List[Dict[str, Any]] = field(default_factory=list)
    request_id: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)


class MCPService:
    """MCP 服务管理器"""
    
    def __init__(self):
        # 活跃的 MCP 连接 {tool_id: MCPConnection}
        self._connections: Dict[str, MCPConnection] = {}
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    async def start_server(
        self,
        tool_id: str,
        command: str,
        args: List[str],
        env: Dict[str, str] = None
    ) -> bool:
        """
        启动 MCP Server 进程
        """
        print(f"\n{'='*50}")
        print(f"🚀 启动 MCP Server")
        print(f"   tool_id: {tool_id}")
        print(f"   command: {command}")
        print(f"   args: {args}")
        print(f"   env: {env}")
        print(f"{'='*50}")
        
        async with self._lock:
            # 如果已存在连接，先关闭
            if tool_id in self._connections:
                print(f"   ⚠️ 已存在连接，先关闭")
                await self._close_connection(tool_id)
            
            try:
                # 合并环境变量
                process_env = os.environ.copy()
                if env:
                    process_env.update(env)
                
                print(f"   📦 创建子进程...")
                
                # 使用 subprocess.Popen（Windows 兼容）
                # Windows 上需要设置 creationflags
                creation_flags = 0
                if sys.platform == 'win32':
                    creation_flags = subprocess.CREATE_NO_WINDOW
                
                process = subprocess.Popen(
                    [command] + args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=process_env,
                    creationflags=creation_flags,
                    bufsize=0  # 无缓冲
                )
                
                print(f"   ✓ 子进程已创建, PID: {process.pid}")
                
                conn = MCPConnection(
                    process=process,
                    tools=[],
                    request_id=0
                )
                
                # 启动 stderr 读取线程（用于调试）
                threading.Thread(
                    target=self._read_stderr_sync,
                    args=(process.stderr, tool_id),
                    daemon=True
                ).start()
                
                # 初始化连接
                print(f"   🔗 初始化 MCP 连接...")
                initialized = await self._initialize_connection(conn)
                if not initialized:
                    print(f"   ❌ 初始化失败")
                    process.terminate()
                    return False
                
                print(f"   ✓ 初始化成功")
                
                # 获取工具列表
                print(f"   📋 获取工具列表...")
                tools = await self._list_tools(conn)
                conn.tools = tools
                print(f"   ✓ 发现 {len(tools)} 个工具")
                for t in tools:
                    print(f"      - {t.get('name')}: {t.get('description', '')[:50]}")
                
                self._connections[tool_id] = conn
                print(f"   ✅ MCP Server 启动成功!")
                return True
                
            except FileNotFoundError as e:
                print(f"   ❌ 命令未找到: {command}")
                print(f"      请确保 {command} 已安装并在 PATH 中")
                return False
            except Exception as e:
                print(f"   ❌ 启动 MCP Server 失败: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def _read_stderr_sync(self, stderr, tool_id: str):
        """同步读取 stderr 输出（在单独线程中运行）"""
        try:
            for line in iter(stderr.readline, b''):
                if not line:
                    break
                print(f"   [MCP {tool_id[:8]} stderr] {line.decode().strip()}")
        except Exception as e:
            pass
    
    async def _initialize_connection(self, conn: MCPConnection) -> bool:
        """发送 initialize 请求"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": self._next_id(conn),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "liuyun-know",
                        "version": "1.0.0"
                    }
                }
            }
            
            print(f"   📤 发送 initialize 请求...")
            response = await self._send_request(conn, request, timeout=30)
            print(f"   📥 收到响应: {json.dumps(response, ensure_ascii=False)[:200] if response else 'None'}")
            
            if response and "result" in response:
                # 发送 initialized 通知
                notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                await self._send_notification(conn, notification)
                return True
            
            if response and "error" in response:
                print(f"   ❌ 初始化错误: {response['error']}")
            
            return False
        except Exception as e:
            print(f"   ❌ MCP 初始化失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _list_tools(self, conn: MCPConnection) -> List[Dict[str, Any]]:
        """获取 MCP Server 提供的工具列表"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": self._next_id(conn),
                "method": "tools/list",
                "params": {}
            }
            
            response = await self._send_request(conn, request, timeout=10)
            if response and "result" in response:
                return response["result"].get("tools", [])
            return []
        except Exception as e:
            print(f"   ❌ 获取工具列表失败: {e}")
            return []
    
    async def call_tool(
        self,
        tool_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用 MCP 工具"""
        conn = self._connections.get(tool_id)
        if not conn:
            return {"error": f"MCP 连接不存在: {tool_id}"}
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": self._next_id(conn),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            print(f"   🔧 调用工具: {tool_name}, 参数: {arguments}")
            response = await self._send_request(conn, request, timeout=60)
            print(f"   📥 工具响应: {json.dumps(response, ensure_ascii=False)[:300] if response else 'None'}")
            
            if response:
                if "error" in response:
                    return {"error": response["error"].get("message", "Unknown error")}
                return response.get("result", {})
            return {"error": "No response from MCP server"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_tools(self, tool_id: str) -> List[Dict[str, Any]]:
        """获取指定 MCP 配置的工具列表"""
        conn = self._connections.get(tool_id)
        if conn:
            return conn.tools
        return []
    
    async def test_connection(
        self,
        command: str,
        args: List[str],
        env: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """测试 MCP 配置是否可用"""
        temp_id = f"test_{uuid.uuid4().hex[:8]}"
        
        print(f"\n🧪 测试 MCP 连接: {command} {' '.join(args)}")
        
        try:
            success = await self.start_server(temp_id, command, args, env)
            if success:
                tools = await self.get_tools(temp_id)
                await self.stop_server(temp_id)
                return {
                    "success": True,
                    "message": f"连接成功，发现 {len(tools)} 个工具",
                    "tools_count": len(tools),
                    "tools": tools
                }
            else:
                return {
                    "success": False,
                    "message": "无法连接到 MCP Server，请检查命令是否正确",
                    "tools_count": 0,
                    "tools": []
                }
        except Exception as e:
            await self.stop_server(temp_id)
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
                "tools_count": 0,
                "tools": []
            }
    
    async def stop_server(self, tool_id: str):
        """停止 MCP Server"""
        async with self._lock:
            await self._close_connection(tool_id)
    
    async def _close_connection(self, tool_id: str):
        """关闭连接"""
        conn = self._connections.pop(tool_id, None)
        if conn:
            try:
                conn.process.terminate()
                conn.process.wait(timeout=5)
            except:
                conn.process.kill()
    
    async def _send_request(
        self,
        conn: MCPConnection,
        request: Dict[str, Any],
        timeout: float = 30
    ) -> Optional[Dict[str, Any]]:
        """发送 JSON-RPC 请求并等待响应（在线程池中执行同步 IO）"""
        
        def sync_send_receive():
            with conn._lock:
                try:
                    # 发送请求
                    message = json.dumps(request) + "\n"
                    conn.process.stdin.write(message.encode())
                    conn.process.stdin.flush()
                    
                    # 读取响应
                    response_line = conn.process.stdout.readline()
                    
                    if response_line:
                        return json.loads(response_line.decode())
                    return None
                except Exception as e:
                    print(f"   ❌ 同步通信错误: {type(e).__name__}: {e}")
                    return None
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(self._executor, sync_send_receive),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            print(f"   ⚠️ MCP 请求超时 ({timeout}s)")
            return None
        except Exception as e:
            print(f"   ❌ MCP 通信错误: {type(e).__name__}: {e}")
            return None
    
    async def _send_notification(self, conn: MCPConnection, notification: Dict[str, Any]):
        """发送 JSON-RPC 通知（不等待响应）"""
        def sync_send():
            with conn._lock:
                try:
                    message = json.dumps(notification) + "\n"
                    conn.process.stdin.write(message.encode())
                    conn.process.stdin.flush()
                except Exception as e:
                    print(f"   ⚠️ 发送通知失败: {e}")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, sync_send)
    
    def _next_id(self, conn: MCPConnection) -> int:
        """生成下一个请求 ID"""
        conn.request_id += 1
        return conn.request_id
    
    def is_connected(self, tool_id: str) -> bool:
        """检查是否已连接"""
        return tool_id in self._connections
    
    async def shutdown(self):
        """关闭所有连接"""
        async with self._lock:
            for tool_id in list(self._connections.keys()):
                await self._close_connection(tool_id)
        self._executor.shutdown(wait=False)


# 全局 MCP 服务实例
mcp_service = MCPService()
