"""
重建 MCP 工具表的脚本
逻辑：如果存在 mcp_tools 表 → 删除 → 重新创建
直接运行: python recreate_mcp_table.py
"""
import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sqlite", "liuyun_know.db")


def recreate_mcp_tools_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 如果表存在，先删除
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='mcp_tools'
    """)
    if cursor.fetchone():
        print("🗑️ 发现 mcp_tools 表，正在删除...")
        cursor.execute("DROP TABLE mcp_tools")

    # 2. 创建表
    print("📦 创建 mcp_tools 表...")
    cursor.execute("""
        CREATE TABLE mcp_tools (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(500),
            tool_type VARCHAR(20) NOT NULL DEFAULT 'user',
            config_json TEXT NOT NULL,
            user_id VARCHAR(36),
            enabled BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 3. 创建索引
    cursor.execute("CREATE INDEX ix_mcp_tools_id ON mcp_tools(id)")
    cursor.execute("CREATE INDEX ix_mcp_tools_name ON mcp_tools(name)")
    cursor.execute("CREATE INDEX ix_mcp_tools_tool_type ON mcp_tools(tool_type)")
    cursor.execute("CREATE INDEX ix_mcp_tools_user_id ON mcp_tools(user_id)")

    conn.commit()
    conn.close()

    print("✅ mcp_tools 表已成功重建！")


if __name__ == "__main__":
    print(f"📂 数据库路径: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        exit(1)

    recreate_mcp_tools_table()
