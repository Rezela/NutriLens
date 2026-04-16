# https://ai.google.dev/gemini-api/docs/image-understanding?hl=zh-cn
"""
图片理解

Gemini 模型从一开始就具有多模态特性，可解锁各种图片处理和计算机视觉任务，包括但不限于图片说明、分类和视觉问答，而无需训练专门的机器学习模型。

除了通用多模态功能外，Gemini 模型还通过额外 训练，针对特定使用情形（例如对象检测和分割）提供 更高的准确率。

将图片传递给 Gemini
您可以使用以下两种方法将图片作为输入提供给 Gemini：

传递内嵌图片数据：非常适合较小的文件（总请求 大小小于 20MB，包括提示）。
使用 File API 上传图片：建议用于较大的文件，或在 多个请求中重复使用图片。
传递内嵌图片数据
您可以在对 generateContent 的请求中传递内嵌图片数据。您可以 Base64 编码字符串的形式提供图片数据，也可以直接读取本地文件（具体取决于语言）。

以下示例展示了如何从本地文件读取图片并将其传递给 generateContent API 进行处理。
"""
from google import genai
from google.genai import types

with open('path/to/small-sample.jpg', 'rb') as f:
    image_bytes = f.read()

client = genai.Client()
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=[
      types.Part.from_bytes(
        data=image_bytes,
        mime_type='image/jpeg',
      ),
      'Caption this image.'
    ]
  )

print(response.text)



# 您还可以从网址提取图片，将其转换为字节，然后将其传递给 generateContent，如以下示例所示。
from google import genai
from google.genai import types

import requests

image_path = "https://goo.gle/instrument-img"
image_bytes = requests.get(image_path).content
image = types.Part.from_bytes(
  data=image_bytes, mime_type="image/jpeg"
)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=["What is this image?", image],
)

print(response.text)



"""
使用 File API 上传图片
对于大文件或需要重复使用同一图片文件的情况，请使用 Files API。以下代码会上传图片文件，然后在对 generateContent 的调用中使用该文件。如需了解 更多信息和示例，请参阅Files API 指南。
"""
from google import genai

client = genai.Client()

my_file = client.files.upload(file="path/to/sample.jpg")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[my_file, "Caption this image."],
)

print(response.text)



"""
使用多张图片进行提示
您可以在单个提示中提供多张图片，方法是在 contents 数组中添加多个图片 Part 对象。这些对象可以是内嵌数据（本地文件或网址）和 File API 引用的组合。
"""
from google import genai
from google.genai import types

client = genai.Client()

# Upload the first image
image1_path = "path/to/image1.jpg"
uploaded_file = client.files.upload(file=image1_path)

# Prepare the second image as inline data
image2_path = "path/to/image2.png"
with open(image2_path, 'rb') as f:
    img2_bytes = f.read()

# Create the prompt with text and multiple images
response = client.models.generate_content(

    model="gemini-3-flash-preview",
    contents=[
        "What is different between these two images?",
        uploaded_file,  # Use the uploaded file reference
        types.Part.from_bytes(
            data=img2_bytes,
            mime_type='image/png'
        )
    ]
)

print(response.text)


"""
对象检测
模型经过训练，可以检测图片中的对象并获取其边界框坐标。相对于图片尺寸的坐标会缩放为 [0, 1000]。您需要根据原始图片大小对这些坐标进行反缩放。
"""
from google import genai
from google.genai import types
from PIL import Image
import json

client = genai.Client()
prompt = "Detect the all of the prominent items in the image. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."

image = Image.open("/path/to/image.png")

config = types.GenerateContentConfig(
  response_mime_type="application/json"
  )

response = client.models.generate_content(model="gemini-3-flash-preview",
                                          contents=[image, prompt],
                                          config=config
                                          )

width, height = image.size
bounding_boxes = json.loads(response.text)

converted_bounding_boxes = []
for bounding_box in bounding_boxes:
    abs_y1 = int(bounding_box["box_2d"][0]/1000 * height)
    abs_x1 = int(bounding_box["box_2d"][1]/1000 * width)
    abs_y2 = int(bounding_box["box_2d"][2]/1000 * height)
    abs_x2 = int(bounding_box["box_2d"][3]/1000 * width)
    converted_bounding_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])

print("Image size: ", width, height)
print("Bounding boxes:", converted_bounding_boxes)

"""
注意： 该模型还支持根据自定义说明生成边界框，例如：“Show bounding boxes of all green objects in this image”。它还支持自定义标签，例如“label the items with the allergens they can contain”。
如需查看更多示例，请查看 Gemini Cookbook 中的以下笔记本：

2D 空间理解笔记本
实验性 3D 指向笔记本
"""



"""
细分
从 Gemini 2.5 开始，模型不仅可以检测商品，还可以分割商品并提供其轮廓蒙版。

该模型会预测 JSON 列表，其中每个项代表一个分割蒙版。每个项都有一个边界框（“box_2d”），格式为 [y0, x0, y1, x1]，其中包含介于 0 到 1000 之间的标准化坐标；一个用于标识对象的标签（“label”）；以及边界框内的分割蒙版，该蒙版是 Base64 编码的 PNG，是一个概率图，其值介于 0 到 255 之间。您需要调整蒙版的大小以匹配边界框尺寸，然后在置信度阈值（中点为 127）处对其进行二值化。

注意： 为了获得更好的结果，请将思考预算设置为 0，以停用思考。如需查看示例，请参阅下面的代码示例。
"""
from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import io
import base64
import json
import numpy as np
import os

client = genai.Client()

def parse_json(json_output: str):
  # Parsing out the markdown fencing
  lines = json_output.splitlines()
  for i, line in enumerate(lines):
    if line == "```json":
      json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
      output = json_output.split("```")[0]  # Remove everything after the closing "```"
      break  # Exit the loop once "```json" is found
  return json_output

def extract_segmentation_masks(image_path: str, output_dir: str = "segmentation_outputs"):
  # Load and resize image
  im = Image.open(image_path)
  im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)

  prompt = """
  Give the segmentation masks for the wooden and glass items.
  Output a JSON list of segmentation masks where each entry contains the 2D
  bounding box in the key "box_2d", the segmentation mask in key "mask", and
  the text label in the key "label". Use descriptive labels.
  """

  config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0) # set thinking_budget to 0 for better results in object detection
  )

  response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[prompt, im], # Pillow images can be directly passed as inputs (which will be converted by the SDK)
    config=config
  )

  # Parse JSON response
  items = json.loads(parse_json(response.text))

  # Create output directory
  os.makedirs(output_dir, exist_ok=True)

  # Process each mask
  for i, item in enumerate(items):
      # Get bounding box coordinates
      box = item["box_2d"]
      y0 = int(box[0] / 1000 * im.size[1])
      x0 = int(box[1] / 1000 * im.size[0])
      y1 = int(box[2] / 1000 * im.size[1])
      x1 = int(box[3] / 1000 * im.size[0])

      # Skip invalid boxes
      if y0 >= y1 or x0 >= x1:
          continue

      # Process mask
      png_str = item["mask"]
      if not png_str.startswith("data:image/png;base64,"):
          continue

      # Remove prefix
      png_str = png_str.removeprefix("data:image/png;base64,")
      mask_data = base64.b64decode(png_str)
      mask = Image.open(io.BytesIO(mask_data))

      # Resize mask to match bounding box
      mask = mask.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR)

      # Convert mask to numpy array for processing
      mask_array = np.array(mask)

      # Create overlay for this mask
      overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
      overlay_draw = ImageDraw.Draw(overlay)

      # Create overlay for the mask
      color = (255, 255, 255, 200)
      for y in range(y0, y1):
          for x in range(x0, x1):
              if mask_array[y - y0, x - x0] > 128:  # Threshold for mask
                  overlay_draw.point((x, y), fill=color)

      # Save individual mask and its overlay
      mask_filename = f"{item['label']}_{i}_mask.png"
      overlay_filename = f"{item['label']}_{i}_overlay.png"

      mask.save(os.path.join(output_dir, mask_filename))

      # Create and save overlay
      composite = Image.alpha_composite(im.convert('RGBA'), overlay)
      composite.save(os.path.join(output_dir, overlay_filename))
      print(f"Saved mask and overlay for {item['label']} to {output_dir}")

# Example usage
if __name__ == "__main__":
  extract_segmentation_masks("path/to/image.png")



"""
支持的图片格式
Gemini 支持以下图片格式 MIME 类型：

PNG - image/png
JPEG - image/jpeg
WEBP - image/webp
HEIC - image/heic
HEIF - image/heif
如需了解其他文件输入方法，请参阅 文件输入方法指南。

功能
所有 Gemini 模型版本都具有多模态特性，可用于各种图片处理和计算机视觉任务，包括但不限于图片说明、视觉问答、图片分类、对象检测和分割。

Gemini 可以减少对专用机器学习模型的需求，具体取决于您的质量和性能要求。

除了通用功能外，最新模型版本还经过专门训练，可提高 专用任务的准确率，例如增强的 对象检测 和 细分。

限制和关键技术信息
文件限制
Gemini 模型每个请求最多支持 3,600 个图片文件。

token 计算
如果两个尺寸均小于或等于 384 像素，则为 258 个 token。 较大的图片会平铺到 768x768 像素的图块中，每个图块需要 258 个 token。
计算图块数量的粗略公式如下：

计算裁剪单元大小，大致为：floor(min(width, height) / 1.5)。
将每个尺寸除以裁剪单元大小，然后将结果相乘，即可得到图块数量。
例如，对于尺寸为 960x540 的图片，裁剪单元大小为 360。将每个尺寸除以 360，图块数量为 3 * 2 = 6。

媒体分辨率
Gemini 3 引入了对多模态视觉处理的精细控制，通过 media_resolution 参数实现。media_resolution 参数用于确定为每个输入图片或视频帧分配的 token 数量上限 。分辨率越高，模型读取精细文本或识别小细节的能力就越强，但 token 用量和延迟也会增加。

如需详细了解该参数及其对 token 计算的影响， 请参阅媒体分辨率指南。

技巧和最佳做法
验证图片是否正确旋转。
使用清晰、不模糊的图片。
如果使用包含文本的单张图片，请在 contents 数组中将文本提示放在图片部分之后 。
后续步骤
本指南介绍了如何上传图片文件并根据图片输入生成文本输出。如需了解详情，请参阅以下资源：

Files API：详细了解如何上传和管理文件以供 Gemini 使用。
系统说明： 系统说明可让您根据 特定需求和使用情形来控制模型的行为。
文件提示策略： Gemini API 支持使用文本、图片、音频和视频数据进行提示，也 称为多模态提示。
安全指南：有时，生成式 AI 模型会生成意外输出，例如不准确、 有偏见或令人反感的输出。后处理和人工评估对于限制此类输出造成的危害风险至关重要。
"""
