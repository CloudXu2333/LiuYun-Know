"""
流程图服务 - 简单工具调用实现

直接生成 Draw.io XML，无需 MCP 协议
"""
import json
import os
from typing import Dict, Any, List
from pathlib import Path


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
    
    # 分析边的连接关系
    outgoing_edges = {}
    incoming_edges = {}
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
        
        source_pos = positions.get(source, (0, 0))
        target_pos = positions.get(target, (0, 0))
        source_size = node_sizes.get(source, (120, 60))
        target_size = node_sizes.get(target, (120, 60))
        
        src_cx = source_pos[0] + source_size[0] / 2
        src_cy = source_pos[1] + source_size[1] / 2
        tgt_cx = target_pos[0] + target_size[0] / 2
        tgt_cy = target_pos[1] + target_size[1] / 2
        
        dx = tgt_cx - src_cx
        dy = tgt_cy - src_cy
        is_back_edge = dy < -20
        is_left = dx < -80
        is_right = dx > 80
        is_same_column = abs(dx) < 80
        
        src_out_count = len(outgoing_edges.get(source, []))
        src_out_edges = outgoing_edges.get(source, [])
        edge_index_in_src = src_out_edges.index(edge) if edge in src_out_edges else 0
        
        style_parts = ["html=1"]
        
        if is_back_edge:
            style_parts.append("edgeStyle=orthogonalEdgeStyle")
            style_parts.append("curved=1")
            style_parts.append("dashed=1")
        elif src_out_count > 1:
            style_parts.append("edgeStyle=orthogonalEdgeStyle")
            style_parts.append("rounded=1")
        else:
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
        
        exitX, exitY, entryX, entryY = 0.5, 1, 0.5, 0
        
        if edge.get('exitX') is not None:
            exitX = edge['exitX']
        elif is_back_edge:
            exitX = 0
        elif is_left:
            exitX = 0
        elif is_right:
            exitX = 1
        elif src_out_count > 1:
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
<mxfile host="app.diagrams.net" agent="Diagram Service">
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


class DiagramService:
    """流程图服务 - 简单工具调用"""
    
    def __init__(self):
        # diagrams 目录
        self.diagrams_dir = Path(__file__).parent.parent.parent / "diagrams"
        self.diagrams_dir.mkdir(exist_ok=True)
    
    def get_tools(self) -> List[Dict]:
        """获取工具定义（OpenAI Function Calling 格式）"""
        return [{
            "type": "function",
            "function": {
                "name": "create_diagram",
                "description": "创建 Draw.io 流程图。当用户要求创建、生成、画流程图时调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "流程图标题"
                        },
                        "nodes": {
                            "type": "array",
                            "description": "节点列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "节点唯一ID"},
                                    "label": {"type": "string", "description": "节点显示文字"},
                                    "x": {"type": "number", "description": "X坐标"},
                                    "y": {"type": "number", "description": "Y坐标"},
                                    "width": {"type": "number", "description": "宽度"},
                                    "height": {"type": "number", "description": "高度"},
                                    "shape": {"type": "string", "description": "形状: ellipse/rectangle/rhombus等"},
                                    "fillColor": {"type": "string", "description": "填充颜色"},
                                    "strokeColor": {"type": "string", "description": "边框颜色"}
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
                                    "label": {"type": "string"}
                                },
                                "required": ["from", "to"]
                            }
                        }
                    },
                    "required": ["title", "nodes", "edges"]
                }
            }
        }]
    
    def create_diagram(self, title: str, nodes: List[Dict], edges: List[Dict], filename: str = None) -> Dict[str, Any]:
        """
        创建流程图
        
        Args:
            title: 流程图标题
            nodes: 节点列表
            edges: 连接线列表
            filename: 文件名（可选）
            
        Returns:
            包含结果的字典
        """
        try:
            if not filename:
                filename = title.replace(" ", "_")
            
            # 生成 XML
            xml_content = generate_drawio_xml(title, nodes, edges)
            
            # 保存文件
            filepath = self.diagrams_dir / f"{filename}.drawio"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            return {
                "success": True,
                "xml": xml_content,
                "filename": str(filepath),
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "message": f"✓ 流程图已生成：{title}（{len(nodes)} 个节点，{len(edges)} 条连接）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"生成流程图失败: {str(e)}"
            }
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具（统一入口）
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        if name == "create_diagram":
            return self.create_diagram(
                title=arguments.get("title", "流程图"),
                nodes=arguments.get("nodes", []),
                edges=arguments.get("edges", []),
                filename=arguments.get("filename")
            )
        else:
            return {"success": False, "error": f"未知工具: {name}"}


# 全局实例
diagram_service = DiagramService()
