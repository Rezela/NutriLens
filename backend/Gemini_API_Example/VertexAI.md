Vertex AI 快速入门

本快速入门将向您介绍如何为您选择的语言安装 Google Gen AI SDK，然后发出您的第一个 API 请求。

要求
Vertex AI 使用入门的要求取决于您的 Google Cloud 工作流。您需要：

新 Google Cloud 用户和快速模式用户：
拥有有效的 @gmail.com Google 账号
注册快速模式
拥有快速模式 API 密钥
在控制台中启用 Vertex AI API
现有用户：
拥有有效的 @gmail.com Google 账号 和 Google Cloud 项目
启用结算功能
在控制台中启用 Vertex AI API
已设置身份验证方法，可以是：
应用默认 凭证 (ADC)， 或
绑定到服务帐号的 API 密钥 that's
注意： Vertex AI 不支持 AI Studio API 密钥。
选择身份验证方法：


API 密钥
准备工作
如果您还没有 API 密钥 ，则需要先获取一个，然后才能 继续。如果您已有 API 密钥，请跳到下一步。

Google Cloud 提供两种类型的 API 密钥：快速模式 API 密钥， 绑定到服务帐号的 API 密钥。您应为此快速入门获取哪种 API 密钥取决于您是否有现有 Google Cloud 项目：

如果您是新手 Google Cloud 或 使用快速模式：创建 快速模式 API 密钥。 如果您是快速模式的新手，则需要先 注册。
如果您已有 Google Cloud 项目：创建绑定到服务帐号的标准 Google Cloud API 密钥 。只有在组织政策设置中启用此功能后，才能将 API 密钥绑定到服务帐号 。如果您无法启用此设置，请改用 ADC。
设置所需角色
如果您使用的是标准 API 密钥或 ADC，则还需要为您的项目授予 Vertex AI 的相应 Identity and Access Management 权限。如果您使用的是 快速模式 API 密钥，则可以跳到下一步。

如需获得使用 Vertex AI 所需的权限，请让您的管理员为您授予项目的Vertex AI User (roles/aiplatform.user) IAM 角色。如需详细了解如何授予角色，请参阅管理对项目、文件夹和组织的访问权限。

您也可以通过自定义角色或其他预定义角色来获取所需的权限。

安装 SDK 并设置环境
在您的本地机器上，点击以下标签页之一，安装相应编程语言的 SDK。

Python
Go
Node.js
Java
REST
运行以下命令，安装并更新 Gen AI SDK for Python。



pip install --upgrade google-genai
设置环境变量：



# Replace the `GOOGLE_CLOUD_PROJECT_ID` and `GOOGLE_CLOUD_LOCATION` values
# with appropriate values for your project.
export GOOGLE_CLOUD_PROJECT=GOOGLE_CLOUD_PROJECT_ID
export GOOGLE_CLOUD_LOCATION=global
export GOOGLE_GENAI_USE_VERTEXAI=True
    
提交第一个请求
使用 generateContent 方法向 Vertex AI 中的 Gemini API 发送请求：

Python
Go
Node.js
Java
C#
REST



from google import genai
from google.genai.types import HttpOptions

client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?",
)
print(response.text)
# Example response:
# Okay, let's break down how AI works. It's a broad field, so I'll focus on the ...
#
# Here's a simplified overview:
# ...
当您使用区域 API 端点（例如 us-central1) 时，端点网址中的区域决定了请求的处理位置。资源路径中任何冲突的位置都会被 忽略。
生成图片
注意：Gemini 图片生成功能目前为预览版。如果您需要可用于生产用途的图片生成功能，请使用 Imagen。如需了解详情，请参阅 Imagen on Vertex AI 快速入门。
Gemini 能够以对话方式生成并处理图片。您可以使用文本、图片或两者结合来向 Gemini 撰写提示，以实现各种与图片相关的任务，例如图片生成和编辑。以下代码演示了如何根据描述性提示生成图片：

您必须在配置中添加 responseModalities: ["TEXT", "IMAGE"]。这些模型不支持仅图片输出。

Python
Go
Node.js
Java



import os
from io import BytesIO

from google import genai
from google.genai.types import GenerateContentConfig, Modality
from PIL import Image

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=("Generate an image of the Eiffel tower with fireworks in the background."),
    config=GenerateContentConfig(
        response_modalities=[Modality.TEXT, Modality.IMAGE],
    ),
)
for part in response.candidates[0].content.parts:
    if part.text:
        print(part.text)
    elif part.inline_data:
        image = Image.open(BytesIO((part.inline_data.data)))
        # Ensure the output directory exists
        output_dir = "output_folder"
        os.makedirs(output_dir, exist_ok=True)
        image.save(os.path.join(output_dir, "example-image-eiffel-tower.png"))
图片理解
Gemini 还可以理解图片。以下代码使用上一部分中生成的图片，并使用不同的模型来推断有关图片的信息：

Python
Go
Node.js
Java



from google import genai
from google.genai.types import HttpOptions, Part

client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        "What is shown in this image?",
        Part.from_uri(
            file_uri="gs://cloud-samples-data/generative-ai/image/scones.jpg",
            mime_type="image/jpeg",
        ),
    ],
)
print(response.text)
# Example response:
# The image shows a flat lay of blueberry scones arranged on parchment paper. There are ...
代码执行
Vertex AI 中的 Gemini API 代码执行功能可让模型生成和运行 Python 代码，并根据相应结果进行迭代学习，直到获得最终输出结果。Vertex AI 提供代码执行作为工具，类似于函数调用。利用此代码执行功能，您可以构建可受益于基于代码的推理并生成文本输出的应用。例如：

Python
Go
Node.js
Java



from google import genai
from google.genai.types import (
    HttpOptions,
    Tool,
    ToolCodeExecution,
    GenerateContentConfig,
)

client = genai.Client(http_options=HttpOptions(api_version="v1"))
model_id = "gemini-2.5-flash"

code_execution_tool = Tool(code_execution=ToolCodeExecution())
response = client.models.generate_content(
    model=model_id,
    contents="Calculate 20th fibonacci number. Then find the nearest palindrome to it.",
    config=GenerateContentConfig(
        tools=[code_execution_tool],
        temperature=0,
    ),
)
print("# Code:")
print(response.executable_code)
print("# Outcome:")
print(response.code_execution_result)

# Example response:
# # Code:
# def fibonacci(n):
#     if n <= 0:
#         return 0
#     elif n == 1:
#         return 1
#     else:
#         a, b = 0, 1
#         for _ in range(2, n + 1):
#             a, b = b, a + b
#         return b
#
# fib_20 = fibonacci(20)
# print(f'{fib_20=}')
#
# # Outcome:
# fib_20=6765
如需查看更多代码执行示例，请参阅代码执行 文档。