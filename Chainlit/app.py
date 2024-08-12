from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI(
    api_key="vllm",
    base_url="http://0.0.0.0:8080/v1",
)

# Instrument the OpenAI client
cl.instrument_openai()

settings = {
    "model": "Qwen2-0.5B-Instruct",
    "max_tokens": 1024,
    "temperature": 0.1,  # 降低温度以减少重复
    "top_p": 0.9,        # 调整 top_p 以控制输出多样性
}

# 增加几个 提示启动器（类似于推荐prompt or chat）
# @cl.set_starters
# async def set_starters():
#     return [
#         cl.Starter(
#             label="Morning routine ideation",
#             message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
#             icon="/public/idea.svg",
#             ),

#         cl.Starter(
#             label="Explain superconductors",
#             message="Explain superconductors like I'm five years old.",
#             icon="/public/learn.svg",
#             ),
#         cl.Starter(
#             label="Python script for daily email reports",
#             message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
#             icon="/public/terminal.svg",
#             ),
#         cl.Starter(
#             label="Text inviting friend to wedding",
#             message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
#             icon="/public/write.svg",
#             )
#         ]

# @cl.on_message
# async def on_message(message: cl.Message):
#     response = await client.chat.completions.create(
#         messages=[
#             {
#                 "content": "You are a helpful bot, you always reply in Chinese",
#                 "role": "system"
#             },
#             {
#                 "content": message.content,
#                 "role": "user"
#             }
#         ],
#         **settings
#     )
#     await cl.Message(content=response.choices[0].message.content).send()


# 流式输出 
@cl.on_chat_start
def start_chat():
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )


@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()