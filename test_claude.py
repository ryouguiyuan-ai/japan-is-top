import os
from dotenv import load_dotenv
from anthropic import Anthropic

# .env から API キーを読み込む
load_dotenv()

# Claude クライアントを作成
client = Anthropic()

# Claude にメッセージを送る
message = client.messages.create(
model="claude-haiku-4-5",
max_tokens=1024,
messages=[
{
"role": "user",
"content": "こんにちは！日本の山で初心者におすすめは？1つだけ、50字以内で答えてください。"
}
]
)

# 返事を表示
print("=" * 50)
print("Claude の返事:")
print("=" * 50)
print(message.content[0].text)
print("=" * 50)

