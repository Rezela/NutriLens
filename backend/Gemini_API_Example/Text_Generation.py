# https://ai.google.dev/gemini-api/docs/text-generation?hl=zh-cn
"""
文本生成
Gemini API 可以根据文本、图片、视频和音频输入生成文本输出。

下面是一个基本示例：
"""
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="How does AI work?"
)
print(response.text)



"""
与 Gemini 一起思考
Gemini 模型通常默认启用“思考”功能，以便模型在回答请求之前进行推理。

每种模型都支持不同的思考配置，让您可以控制费用、延迟时间和智能程度。如需了解详情，请参阅思维指南。
"""
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="How does AI work?",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="low")
    ),
)
print(response.text)



"""
系统指令和其他配置
您可以使用系统指令来引导 Gemini 模型的行为。为此，请传递一个 GenerateContentConfig 对象。
"""
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        system_instruction="You are a cat. Your name is Neko."),
    contents="Hello there"
)

print(response.text)



"""
借助 GenerateContentConfig 对象，您还可以替换默认的生成参数，例如温度。

使用 Gemini 3 模型时，我们强烈建议将 temperature 保留为默认值 1.0。更改温度（将其设置为低于 1.0）可能会导致意外行为（例如循环或性能下降），尤其是在复杂的数学或推理任务中。
"""
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=["Explain how AI works"],
    config=types.GenerateContentConfig(
        temperature=0.1
    )
)
print(response.text)



"""
如需查看可配置参数及其说明的完整列表，请参阅 API 参考文档中的 GenerateContentConfig。

多模态输入
Gemini API 支持多模态输入，让您可以将文本与媒体文件相结合。以下示例演示了如何提供图片：
"""
from PIL import Image
from google import genai

client = genai.Client()

image = Image.open("/path/to/organ.png")
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, "Tell me about this instrument"]
)
print(response.text)



"""
如需了解提供图片的其他方法和更高级的图片处理功能，请参阅我们的图片理解指南。该 API 还支持文档、视频和音频输入和理解。

流式响应
默认情况下，模型仅在整个生成过程完成后才返回回答。

为了获得更流畅的互动体验，请使用流式传输来逐步接收 GenerateContentResponse 实例（在生成时）。
"""
from google import genai

client = genai.Client()

response = client.models.generate_content_stream(
    model="gemini-3-flash-preview",
    contents=["Explain how AI works"]
)
for chunk in response:
    print(chunk.text, end="")



"""
多轮对话（聊天）
我们的 SDK 提供相应功能，可将多轮提示和回答收集到聊天中，让您轻松跟踪对话历史记录。

注意： 聊天功能仅作为 SDK 的一部分实现。在幕后，它仍使用 generateContent API。对于多轮对话，系统会在每个后续轮次中将完整的对话记录发送给模型。
"""
from google import genai

client = genai.Client()
chat = client.chats.create(model="gemini-3-flash-preview")

response = chat.send_message("I have 2 dogs in my house.")
print(response.text)

response = chat.send_message("How many paws are in my house?")
print(response.text)

for message in chat.get_history():
    print(f'role - {message.role}',end=": ")
    print(message.parts[0].text)



# 流式传输还可用于多轮对话。
from google import genai

client = genai.Client()
chat = client.chats.create(model="gemini-3-flash-preview")

response = chat.send_message_stream("I have 2 dogs in my house.")
for chunk in response:
    print(chunk.text, end="")

response = chat.send_message_stream("How many paws are in my house?")
for chunk in response:
    print(chunk.text, end="")

for message in chat.get_history():
    print(f'role - {message.role}', end=": ")
    print(message.parts[0].text)
"""
撰写提示的技巧！
如需了解如何充分利用 Gemini，请参阅我们的提示工程指南。

后续步骤
在 Google AI Studio 中试用 Gemini。
尝试使用结构化输出来生成类似 JSON 的回答。
探索 Gemini 的图片、视频、音频和文档理解功能。
了解多模态文件提示策略。
"""