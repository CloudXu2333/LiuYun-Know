import base64
import os
import requests
import json
import re
from pathlib import Path

class PaddleOCRVL:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token

    def process_pdf(self, file_path: str, output_root: str = "output") -> str:
        """
        使用 PaddleOCR-VL API 处理 PDF 文件。
        
        参数:
            file_path: 本地 PDF 文件路径。
            output_root: 输出根目录。
            
        返回:
            提取的带有图片占位符的文本内容。
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")

        file_name = os.path.splitext(os.path.basename(file_path))[0]
        doc_output_dir = os.path.join(output_root, file_name)
        os.makedirs(doc_output_dir, exist_ok=True)

        # 准备请求
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        # 对于 PDF 文档，设置 `fileType` 为 0；对于图片，设置 `fileType` 为 1
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

        print(f"正在向 {self.api_url} 发送请求，处理文件 {file_path} ...")
        response = requests.post(self.api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise RuntimeError(f"API 请求失败，状态码 {response.status_code}: {response.text}")

        result = response.json().get("result", {})
        if not result:
            return ""

        full_content = []
        
        layout_results = result.get("layoutParsingResults", [])
        if not layout_results:
            print("未找到版面解析结果。")
            return ""

        for i, res in enumerate(layout_results):
            page_num = i + 1
            page_dir = os.path.join(doc_output_dir, f"page{page_num}")
            os.makedirs(page_dir, exist_ok=True)
            
            markdown_data = res.get("markdown", {})
            text = markdown_data.get("text", "")
            images = markdown_data.get("images", {})
            
            # 页面文件夹内的图片目录
            # 为了整洁，我们将它们放在 'images' 子文件夹中
            page_img_dir = os.path.join(page_dir, "images")
            
            # 如果有图片，进行处理
            if images:
                os.makedirs(page_img_dir, exist_ok=True)
                for img_rel_path, img_url in images.items():
                    # img_rel_path 通常像 "images/xxx.jpg" 或 "xxx.jpg"
                    # 我们需要将其映射到我们的本地结构
                    
                    # 从键或 URL 中提取文件名
                    img_filename = os.path.basename(img_rel_path)
                    local_img_path = os.path.join(page_img_dir, img_filename)
                    
                    # 下载图片
                    try:
                        img_resp = requests.get(img_url)
                        if img_resp.status_code == 200:
                            with open(local_img_path, "wb") as f:
                                f.write(img_resp.content)
                            
                            # 生成图片描述 (暂时禁用)
                            # print(f"正在生成图片描述: {img_filename} ...")
                            # description = generate_image_description(local_img_path)
                            # print(f"描述: {description[:30]}...")
                            
                        else:
                            print(f"下载图片失败: {img_url}")
                            # description = "图片下载失败"
                    except Exception as e:
                        print(f"下载图片出错 {img_url}: {e}")
                        # description = f"图片处理出错: {e}"
                    
                    # 更新文本以引用本地图片
                    # 原始文本引用 `img_rel_path`。我们希望它是相对于 Markdown 文件的。
                    # Markdown 文件位于 `page_dir`。图片位于 `page_dir/images`。
                    # 所以相对路径是 `images/img_filename`。
                    
                    # 修改图片路径格式为：pdf名字/pageX/images/xxx.jpg
                    new_rel_path = f"{file_name}/page{page_num}/images/{img_filename}"
                    
                    # 替换图片路径
                    text = text.replace(img_rel_path, new_rel_path)
                    
                    # 然后用正则在图片标签后面插入描述 (暂时禁用)
                    # 匹配刚刚替换过的路径所在的 img 标签
                    # escaped_path = re.escape(new_rel_path)
                    # img_tag_pattern = re.compile(f'(<img[^>]*src="{escaped_path}"[^>]*>)')
                    # text = img_tag_pattern.sub(f'\\1\n> **[图片描述]**: {description}\n', text)

            # 尝试合并图片和其标题（减少中间的空行）
            # 匹配 </div> 后面跟着空白字符，然后是 <div
            text = re.sub(r'(<div[^>]*><img[^>]*></div>)\s+(<div)', r'\1\n\2', text)

            # 保存 Markdown 文件 (暂时禁用)
            # md_path = os.path.join(page_dir, "content.md")
            # with open(md_path, "w", encoding="utf-8") as f:
            #     f.write(text)
            # print(f"已将第 {page_num} 页内容保存到 {md_path}")
            
            full_content.append(f"--- 第 {page_num} 页 ---\n{text}")

        full_text = "\n\n".join(full_content)
        
        # 保存完整文本到 TXT 文件
        txt_path = os.path.join(doc_output_dir, "full_text.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"已将完整文本内容保存到 {txt_path}")

        return full_text

# 配置（从环境变量读取）
import os
from dotenv import load_dotenv
load_dotenv()

API_URL = os.getenv("PADDLEOCR_API_URL", "https://xbmbgatds3k3k5d5.aistudio-app.com/layout-parsing")
TOKEN = os.getenv("PADDLEOCR_TOKEN", "")

def main():
    # 示例用法
    file_path = r"d:\Desktop\learn\lightrag\aaa.pdf"
    # 或者使用命令行参数
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    processor = PaddleOCRVL(API_URL, TOKEN)
    
    try:
        print(f"正在处理 {file_path} ...")
        content = processor.process_pdf(file_path)
        print("\n--- 提取的内容（预览） ---")
        print(content[:500] + "..." if len(content) > 500 else content)
        print("\n处理完成。")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
