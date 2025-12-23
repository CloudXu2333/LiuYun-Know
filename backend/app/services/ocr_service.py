"""
PaddleOCR 文档处理服务
"""
import os
import base64
import requests
from typing import Optional


class OCRService:
    """OCR 服务类 - 使用 PaddleOCR-VL API"""
    
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token
    
    def process_pdf(self, file_path: str, output_dir: str) -> str:
        """
        处理 PDF 文件，提取文本和图片
        
        Args:
            file_path: PDF 文件路径
            output_dir: 输出目录
            
        Returns:
            提取的文本内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 读取文件并编码
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")
        
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }
        
        is_pdf = file_path.lower().endswith('.pdf')
        payload = {
            "file": file_data,
            "fileType": 0 if is_pdf else 1,
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useChartRecognition": False,
            "extra": {
                "max_num_input_imgs": None
            }
        }
        
        print(f"📄 正在处理文件: {file_path}")
        response = requests.post(self.api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise RuntimeError(f"OCR API 请求失败，状态码 {response.status_code}: {response.text}")
        
        result = response.json().get("result", {})
        if not result:
            return ""
        
        full_content = []
        layout_results = result.get("layoutParsingResults", [])
        
        for i, res in enumerate(layout_results):
            page_num = i + 1
            markdown_data = res.get("markdown", {})
            text = markdown_data.get("text", "")
            images = markdown_data.get("images", {})
            
            # 保存图片
            if images:
                page_img_dir = os.path.join(output_dir, f"page{page_num}", "images")
                os.makedirs(page_img_dir, exist_ok=True)
                
                for img_rel_path, img_url in images.items():
                    img_filename = os.path.basename(img_rel_path)
                    local_img_path = os.path.join(page_img_dir, img_filename)
                    
                    try:
                        img_resp = requests.get(img_url)
                        if img_resp.status_code == 200:
                            with open(local_img_path, "wb") as f:
                                f.write(img_resp.content)
                    except Exception as e:
                        print(f"⚠️ 下载图片失败 {img_url}: {e}")
            
            full_content.append(f"--- 第 {page_num} 页 ---\n{text}")
        
        full_text = "\n\n".join(full_content)
        
        # 保存完整文本
        txt_path = os.path.join(output_dir, "extracted_text.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print(f"✅ 文本提取完成，保存到: {txt_path}")
        return full_text
    
    def process_image(self, file_path: str, output_dir: str) -> str:
        """
        处理图片文件，提取文本
        
        Args:
            file_path: 图片文件路径
            output_dir: 输出目录
            
        Returns:
            提取的文本内容
        """
        return self.process_pdf(file_path, output_dir)


# 从配置创建全局实例
def get_ocr_service() -> Optional[OCRService]:
    """获取 OCR 服务实例"""
    from app.config import settings
    
    api_url = settings.paddleocr_api_url
    token = settings.paddleocr_token
    
    print(f"🔍 OCR 服务配置检查:")
    print(f"   - API URL: {api_url}")
    print(f"   - Token: {'已配置' if token else '未配置'}")
    
    if api_url and token:
        print(f"✅ OCR 服务已初始化")
        return OCRService(api_url, token)
    
    print(f"⚠️ OCR 服务未配置（缺少 PADDLEOCR_TOKEN）")
    return None


ocr_service = get_ocr_service()
