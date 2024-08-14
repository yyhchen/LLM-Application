import chainlit as cl
from chainlit.input_widget import Select
from openai import AsyncOpenAI
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from typing import Optional

client = AsyncOpenAI(
    api_key="vllm",
    base_url="http://0.0.0.0:8080/v1",
)

# Instrument the OpenAI client
cl.instrument_openai()

settings = {
    # "model": "Qwen2-0.5B-Instruct",   # 利用chat_profile 指定模型
    "max_tokens": 512,
    "temperature": 0.1,  # 降低温度以减少重复
    "top_p": 0.9,        # 调整 top_p 以控制输出多样性
}


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("yhchen", "123456"):
        return cl.User(identifier=username, metadata={"role": username, "provider": "credentials"})
    else:
        return None


"""
############################################################################################################
    增加几个 提示启动器 (类似于推荐prompt or chat)
############################################################################################################
"""
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="早晨例行程序构想",
            message="你能帮我创建一个个性化的早晨例行程序吗？这能帮助我在一天中提高生产力。先问我关于我现在的习惯以及哪些活动能在早上给我带来活力。",
            icon="/public/idea.svg",
            ),

        cl.Starter(
            label="像五岁小孩一样解释超导体",
            message="像对五岁小孩解释一样简单地说明什么是超导体。",
            icon="/public/learn.svg",
            ),
        cl.Starter(
            label="用于每日邮件报告的Python脚本",
            message="编写一个Python脚本来自动化发送每日邮件报告，并指导我如何设置。",
            icon="/public/terminal.svg",
            ),
        cl.Starter(
            label="邀请朋友参加婚礼的短信",
            message="写一条短信，邀请朋友下个月作为我的伴郎参加婚礼。我希望保持非常简短和随意的风格，并提供一个婉拒的选项。",
            icon="/public/write.svg",
            )
        ]


"""
############################################################################################################
        聊天配置文件
############################################################################################################
"""
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="Qwen2-0.5B-Instruct",
            markdown_description="The underlying LLM model is **Qwen2-0.5B-Instruct**.",
            icon="/public/qwen.png",
        ),
        cl.ChatProfile(
            name="Qwen2-72B-Instruct",
            markdown_description="The underlying LLM model is **Qwen2-72B-Instruct**.",
            icon="/public/qwen.png",
        ),
        cl.ChatProfile(
            name="Gemma2",
            markdown_description="The underlying LLM model is **Gemma2**.",
            icon="/public/google.png",
        ),
        cl.ChatProfile(
            name="Phi-3",
            markdown_description="The underlying LLM model is **Phi-3**.",
            icon="/public/microsoft.png",
        ),
        cl.ChatProfile(
            name="Llama3",
            markdown_description="The underlying LLM model is **Llama3**.",
            icon="/public/meta.png",
        ),
    ]



"""
############################################################################################################
    聊天框 功能, 模板等设置
############################################################################################################
"""
@cl.on_chat_start
# 对话模板
async def on_chat_start():
    app_user = cl.user_session.get("user")
    await cl.Message(f"Hello {app_user.identifier}").send()

    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )
    


"""
############################################################################################################
    流式输出
############################################################################################################
"""
@cl.on_message
async def main(message: cl.Message):
    # 获取聊天配置中指定的模型
    chat_profile = cl.user_session.get("chat_profile")

    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        model = chat_profile, messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()
