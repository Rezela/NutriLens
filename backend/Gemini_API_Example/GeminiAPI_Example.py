"""
安装 Google GenAI SDK
使用 Python 3.9+，使用以下 pip 命令安装 google-genai 软件包：
pip install -q -U google-genai

提交第一个请求
以下示例使用 generateContent方法 向 Gemini API 发送请求，使用 Gemini 2.5 Flash 模型。
如果您将 API 密钥 设置为 环境变量 GEMINI_API_KEY，则在使用 Gemini API 库 时，客户端会自动提取该密钥。 否则，您需要在初始化客户端时将 API 密钥 作为 实参传递。
请注意，Gemini API 文档中的所有代码示例都假定您已设置环境变量 GEMINI_API_KEY。
"""

from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain how AI works in a few words",
)

print(response.text)