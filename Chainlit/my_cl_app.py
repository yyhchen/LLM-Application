# import chainlit as cl

# @cl.on_chat_start
# async def main():
#     await cl.Message(content="Hello World").send()

from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain import hub
from langchain_openai import ChatOpenAI
import os
import chainlit as cl
from langchain.memory import ConversationBufferMemory

os.environ["LANGCHAIN_API_KEY"] = ''


# Initializing Components
llm = ChatOpenAI(
    temperature=0.95,
    model="glm-4-airx",
    openai_api_key="",    # 加入 API-KEY
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
)

search = DuckDuckGoSearchRun(max_results=2)

tools = [search]

prompt = hub.pull("hwchase17/openai-functions-agent")

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="output")

agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory) 


# Chainlit Callbacks and Runnable
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("agent_executor", agent_executor)

@cl.on_message
async def on_message(message: cl.Message):
    agent_executor = cl.user_session.get("agent_executor")  # type: AgentExecutor
    msg = cl.Message(content="")

    input_data = {"input": message.content}
    result = agent_executor.invoke(input_data)['output']
    
    for char in result:
        await msg.stream_token(char)
    # await msg.stream_token(result)

    await msg.send()

