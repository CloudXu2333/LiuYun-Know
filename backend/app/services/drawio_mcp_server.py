#!/usr/bin/env python3
"""
Draw.io MCP Server - 提供流程图生成工具
通过 MCP 协议暴露 create_diagram 工具
"""
import json
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent

# 初始化 MCP Server
app = Server("drawio-server")

# 形状样式映射
SHAPE_STYLES = {
    'ellipse': 'ellipse;whiteSpace=wrap;html=1;',
    'rectangle': 'whiteSpace=wrap;html=1;',
    'rhombus': 'rhombus;whiteSpace=wrap;html=1;',
    'parallelogram': 'shape=parallelogram;whiteSpace=wrap;html=1;',
    'cylinder': 'shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;',
    'document': 'shape=document;whiteSpace=wrap;html=1;boundedLbl=1;',
    'hexagon': 'shape=hexagon;whiteSpace=wrap;html=1;',
    'triangle': 'triangle;whiteSpace=wrap;html=1;',
    'cloud': 'ellipse;shape=cloud;whiteSpace=wrap;html=1;',
    'actor': 'shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;',
    'step': 'shape=step;whiteSpace=wrap;html=1;fixedSize=1;',
    'tape': 'shape=tape;whiteSpace=wrap;html=1;',
    'note': 'shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;darkOpacity=0.05;',
    'card': 'shape=card;whiteSpace=wrap;html=1;',
    'callout': 'shape=callout;whiteSpace=wrap;html=1;perimeter=calloutPerimeter;',
    'process': 'shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;',
}


def generate_drawio_xml(title: str, nodes: list, edges: list) -> str:
    """生成 Draw.io XML，带智能布局优化"""
    cells = []
    
    # 添加标题
    cells.append(f'''
        <mxCell id="title" value="{title}" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=20;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="200" y="10" width="500" height="40" as="geometry" />
        </mxCell>''')
    
    # 记录节点位置和尺寸
    positions = {}
    node_sizes = {}
    
    # 生成节点
    for node in nodes:
        node_id = node['id']
        label = node.get('label', '').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        x = node.get('x', 400)
        y = node.get('y', 100)
        width = node.get('width', 120)
        height = node.get('height', 60)
        shape = node.get('shape', 'rectangle')
        
        positions[node_id] = (x, y)
        node_sizes[node_id] = (width, height)
        
        # 构建样式
        base_style = SHAPE_STYLES.get(shape, SHAPE_STYLES['rectangle'])
        style_parts = [base_style]

        # 填充样式
        if node.get('fillColor'):
            style_parts.append(f"fillColor={node['fillColor']}")
        if node.get('gradientColor'):
            style_parts.append(f"gradientColor={node['gradientColor']}")
        if node.get('strokeColor'):
            style_parts.append(f"strokeColor={node['strokeColor']}")
        if node.get('strokeWidth'):
            style_parts.append(f"strokeWidth={node['strokeWidth']}")
        if node.get('dashed'):
            style_parts.append("dashed=1")
        if node.get('rounded'):
            style_parts.append("rounded=1")
        if node.get('shadow'):
            style_parts.append("shadow=1")
        if node.get('fontColor'):
            style_parts.append(f"fontColor={node['fontColor']}")
        if node.get('fontSize'):
            style_parts.append(f"fontSize={node['fontSize']}")
        if node.get('fontStyle') is not None:
            style_parts.append(f"fontStyle={node['fontStyle']}")
        if node.get('opacity') is not None:
            style_parts.append(f"opacity={node['opacity']}")
        
        style = ";".join(style_parts) + ";"
        
        cells.append(f'''
        <mxCell id="{node_id}" value="{label}" style="{style}" vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />
        </mxCell>''')
    
    # 分析边的连接关系，用于智能路由
    outgoing_edges = {}  # 每个节点的出边
    incoming_edges = {}  # 每个节点的入边
    for edge in edges:
        src = edge['from']
        tgt = edge['to']
        outgoing_edges.setdefault(src, []).append(edge)
        incoming_edges.setdefault(tgt, []).append(edge)
    
    # 生成连接线
    for idx, edge in enumerate(edges):
        edge_id = f"edge_{idx}"
        source = edge['from']
        target = edge['to']
        label = edge.get('label', '').replace('"', '&quot;')
        
        # 获取位置和尺寸
        source_pos = positions.get(source, (0, 0))
        target_pos = positions.get(target, (0, 0))
        source_size = node_sizes.get(source, (120, 60))
        target_size = node_sizes.get(target, (120, 60))
        
        # 计算节点中心
        src_cx = source_pos[0] + source_size[0] / 2
        src_cy = source_pos[1] + source_size[1] / 2
        tgt_cx = target_pos[0] + target_size[0] / 2
        tgt_cy = target_pos[1] + target_size[1] / 2
        
        # 判断方向
        dx = tgt_cx - src_cx
        dy = tgt_cy - src_cy
        is_back_edge = dy < -20  # 向上的回边
        is_left = dx < -80
        is_right = dx > 80
        is_same_column = abs(dx) < 80
        
        # 检查是否有多条出边（分支）
        src_out_count = len(outgoing_edges.get(source, []))
        src_out_edges = outgoing_edges.get(source, [])
        edge_index_in_src = src_out_edges.index(edge) if edge in src_out_edges else 0
        
        style_parts = ["html=1"]
        
        # 选择边样式
        if is_back_edge:
            # 回边使用曲线，避免穿过其他节点
            style_parts.append("edgeStyle=orthogonalEdgeStyle")
            style_parts.append("curved=1")
            style_parts.append("dashed=1")
        elif src_out_count > 1:
            # 多分支使用正交边
            style_parts.append("edgeStyle=orthogonalEdgeStyle")
            style_parts.append("rounded=1")
        else:
            # 普通边
            style_parts.append("edgeStyle=orthogonalEdgeStyle")
            if edge.get('curved'):
                style_parts.append("curved=1")
            if edge.get('rounded'):
                style_parts.append("rounded=1")
        
        style_parts.append(f"strokeColor={edge.get('strokeColor', '#333333')}")
        style_parts.append(f"strokeWidth={edge.get('strokeWidth', 2)}")
        
        if edge.get('dashed'):
            style_parts.append("dashed=1")
        
        style_parts.append(f"endArrow={edge.get('endArrow', 'classic')}")
        
        # 智能计算连接点
        exitX, exitY, entryX, entryY = 0.5, 1, 0.5, 0  # 默认：下出上入
        
        if edge.get('exitX') is not None:
            exitX = edge['exitX']
        elif is_back_edge:
            # 回边：从左侧出，到左侧入
            exitX = 0
        elif is_left:
            exitX = 0
        elif is_right:
            exitX = 1
        elif src_out_count > 1:
            # 多分支：根据索引分配出口
            if src_out_count == 2:
                exitX = 0 if edge_index_in_src == 0 else 1
            else:
                exitX = edge_index_in_src / (src_out_count - 1) if src_out_count > 1 else 0.5
        
        if edge.get('exitY') is not None:
            exitY = edge['exitY']
        elif is_back_edge:
            exitY = 0.5
        elif is_left or is_right:
            exitY = 0.5
        elif src_out_count > 1 and not is_same_column:
            exitY = 0.5
        
        if edge.get('entryX') is not None:
            entryX = edge['entryX']
        elif is_back_edge:
            entryX = 0
        elif is_left:
            entryX = 1
        elif is_right:
            entryX = 0
        
        if edge.get('entryY') is not None:
            entryY = edge['entryY']
        elif is_back_edge:
            entryY = 0.5
        elif is_left or is_right:
            entryY = 0.5
        
        style_parts.append(f"exitX={exitX}")
        style_parts.append(f"exitY={exitY}")
        style_parts.append(f"entryX={entryX}")
        style_parts.append(f"entryY={entryY}")
        
        # 添加路由点避免交叉（对于回边和横向边）
        if is_back_edge or (is_left and abs(dy) > 50) or (is_right and abs(dy) > 50):
            style_parts.append("jettySize=auto")
            style_parts.append("orthogonalLoop=1")
        
        style_parts.append("labelBackgroundColor=#ffffff")
        style_parts.append("fontSize=11")
        
        style = ";".join(style_parts) + ";"
        label_attr = f'value="{label}"' if label else ''
        
        cells.append(f'''
        <mxCell id="{edge_id}" {label_attr} style="{style}" edge="1" parent="1" source="{source}" target="{target}">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>''')
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" agent="MCP Server">
  <diagram name="Page-1" id="page1">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1000" pageHeight="1200">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />{''.join(cells)}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    
    return xml


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="create_diagram",
            description="创建 Draw.io 流程图，支持完整的节点和边参数",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "流程图标题"},
                    "nodes": {
                        "type": "array",
                        "description": "节点列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "width": {"type": "number"},
                                "height": {"type": "number"},
                                "shape": {"type": "string", "description": "ellipse/rectangle/rhombus/parallelogram/cylinder/document/hexagon/cloud/note"},
                                "fillColor": {"type": "string"},
                                "strokeColor": {"type": "string"},
                                "fontColor": {"type": "string"},
                                "fontSize": {"type": "number"},
                                "rounded": {"type": "boolean"},
                                "shadow": {"type": "boolean"}
                            },
                            "required": ["id", "label", "x", "y", "width", "height", "shape", "fillColor", "strokeColor"]
                        }
                    },
                    "edges": {
                        "type": "array",
                        "description": "连接线列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from": {"type": "string"},
                                "to": {"type": "string"},
                                "label": {"type": "string"},
                                "strokeColor": {"type": "string"},
                                "strokeWidth": {"type": "number"},
                                "dashed": {"type": "boolean"},
                                "curved": {"type": "boolean"},
                                "exitX": {"type": "number"},
                                "exitY": {"type": "number"},
                                "entryX": {"type": "number"},
                                "entryY": {"type": "number"}
                            },
                            "required": ["from", "to"]
                        }
                    },
                    "filename": {"type": "string", "description": "保存的文件名（不含扩展名）"}
                },
                "required": ["title", "nodes", "edges"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理工具调用"""
    
    if name == "create_diagram":
        title = arguments.get("title", "流程图")
        nodes = arguments.get("nodes", [])
        edges = arguments.get("edges", [])
        filename = arguments.get("filename", title.replace(" ", "_"))
        
        # 生成 XML
        xml_content = generate_drawio_xml(title, nodes, edges)
        
        # 确保 diagrams 目录存在
        import os
        diagrams_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "diagrams")
        os.makedirs(diagrams_dir, exist_ok=True)
        
        # 保存文件到 diagrams 目录
        filepath = os.path.join(diagrams_dir, f"{filename}.drawio")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "xml": xml_content,
                    "filename": filepath,
                    "nodes_count": len(nodes),
                    "edges_count": len(edges),
                    "message": f"✓ 流程图已生成：{title}（{len(nodes)} 个节点，{len(edges)} 条连接）"
                }, ensure_ascii=False)
            )
        ]
    
    return [TextContent(type="text", text=f"未知工具: {name}")]


async def main():
    """启动 MCP Server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
