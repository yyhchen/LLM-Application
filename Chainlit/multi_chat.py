from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
import chainlit as cl
from openai import AsyncOpenAI

from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
from langchain.callbacks.base import BaseCallbackHandler
from langchain.indexes import SQLRecordManager, index
from CustomEmbeddings import BGEEmbeddings

DATA_PATH = './data'
EMBED_MODEL_PATH = '/home/yhchen/huggingface_model/BAAI/bge-m3'
MODEL_BASE_URL = "http://localhost:8080/v1"
MODEL_API_KEY = "token-qwen2"
MODEL_NAME = "Qwen2"
EMBEDDING_MODEL_NAME = "bge-m3"
EMBEDDING_BASE_ULR = "http://localhost:8200/v1/embeddings"

"""
############################################################################################################
    一些会使用到的 通用函数
############################################################################################################
"""
def LLM_Client():
    client = AsyncOpenAI(
        api_key=MODEL_API_KEY, # vllm
        base_url=MODEL_BASE_URL,
    )
    settings = {
        # "model": "Qwen2-0.5B-Instruct",   # 利用chat_profile 指定模型
        "max_tokens": 512,
        "temperature": 0.1,  # 降低温度以减少重复
        "top_p": 0.9,        # 调整 top_p 以控制输出多样性
    }
    return client, settings


def Process_Data_Create_Retriever(data_path: str, embed_model_path: str):
    """
        处理数据, 并创建 retriever(检索器) 
    """
    loader = DirectoryLoader(data_path, glob="*.txt")
    docs = loader.load()
    documents = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100).split_documents(docs)

    # embeddings = HuggingFaceBgeEmbeddings(model_name=embed_model_path)
    embeddings = BGEEmbeddings(base_url=EMBEDDING_BASE_ULR, model_name=EMBEDDING_MODEL_NAME)

    vectordb = Chroma.from_documents(documents=documents, embedding=embeddings, collection_name="mydata")
    retriever = vectordb.as_retriever()

    # 将 chroma的数据及数据关系作为索引存储到 SQLite中 (提高索引速度的关键)
    namespace = "chromadb/my_documents"
    record_manager = SQLRecordManager(
        namespace, db_url="sqlite:///record_manager_cache.sql"
    )
    record_manager.create_schema()

    index_result = index(
        docs,
        record_manager,
        vectordb,
        cleanup="incremental",
        source_id_key="source",
    )

    print(f"Indexing stats: {index_result}")

    return retriever


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
            name="Qwen2-RAG",
            markdown_description="The underlying LLM model is **Qwen2-72B-Instruct-GPTQ-INT4**.",
            icon="/public/qwen.png",
        ),
        cl.ChatProfile(
            name="Qwen2",
            markdown_description="The underlying LLM model is **Qwen2-72B-Instruct-GPTQ-INT4**.",
            icon="/public/qwen.png",
        ),
        cl.ChatProfile(
            name="Qwen2-LC",
            markdown_description="The underlying LLM model is **Qwen2-72B-Instruct-GPTQ-INT4w**.",
            icon="/public/qwen.png",
        ),
        cl.ChatProfile(
            name="GraphRAG-latest-global",
            markdown_description="The underlying LLM model is **Phi-3**.",
            icon="/public/microsoft.png",
        ),
        cl.ChatProfile(
            name="20240815-122404-local",
            markdown_description="The underlying LLM model is **Gemma2**.",
            icon="/public/google.png",
        ),
        cl.ChatProfile(
            name="20240815-122404-global",
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
    @cl.on_chat_start 中 不同功能模型封装 (新增模型需要添加)
############################################################################################################
"""
def LC_Chat_Model():
    """
        model chat of RAG (based langchain)
    """
    model = ChatOpenAI(
            base_url= MODEL_BASE_URL,
            api_key = MODEL_API_KEY,
            model = MODEL_NAME,
            streaming=True,
            )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个聪明的人工智能助手，能够回答任何事情",
            ),
            ("human", "{question}"),
        ]
    )
    runnable = prompt | model | StrOutputParser()

    return runnable


def RAG_Chat_Model(data_path, embed_mode_path):
    """
        RAG model chat
    """
    model = ChatOpenAI(
            base_url= MODEL_BASE_URL,
            api_key = MODEL_API_KEY,
            model = MODEL_NAME,
            streaming=True,
            )
    
    system_prompt = (
        "您是一个用于问答任务的助手。"
        "使用以下检索到的上下文片段来回答问题。"
        "如果您不知道答案，请说您不知道，不要猜测回答。"
        "最多使用五句话，尽量保持回答简洁。"
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{question}")
        ]
    )

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    retriever = Process_Data_Create_Retriever(data_path, embed_mode_path)

    runnable = (
        {"context": retriever | format_docs, "question":RunnablePassthrough()} | prompt | model | StrOutputParser()
        )
    return runnable


def GraphRAG_Local_Model():
    """
        local search of GraphRAG
    """
    pass



"""
############################################################################################################
    
                                ==================
                                = Chainlit 装饰器 =   
                                ==================

    聊天框 功能, 模板, langchain 集成 等 (新增模型需要添加)

############################################################################################################
"""
@cl.on_chat_start
async def on_chat_start():
    # 从选择的模型判断 使用功能
    model_name = cl.user_session.get("chat_profile")

    if(model_name == 'Qwen2-LC'):
        runnable = LC_Chat_Model()
        cl.user_session.set("runnable", runnable)
    
    elif (model_name == 'Qwen2'):
        cl.user_session.set(
            "message_history",
            [{"role": "system", "content": "You are a helpful assistant."}],
        )
    elif (model_name == "Qwen2-RAG"):
        runnable = RAG_Chat_Model(DATA_PATH, EMBED_MODEL_PATH)
        cl.user_session.set("runnable", runnable)
        pass



"""
############################################################################################################
    @cl.on_message 中 不同功能模型封装  (新增模型需要添加)
############################################################################################################
"""
async def LC_Chat_Message(message):
    """
        使用 langchain 实现的聊天对话
    """
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()



async def Chat_Model_Message(message):
    """
        original model chat message
    """
    # 获取聊天配置中指定的模型
    chat_profile = cl.user_session.get("chat_profile")

    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    client, settings = LLM_Client()

    stream = await client.chat.completions.create(
        model = chat_profile, messages=message_history,stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()



async def RAG_Chat_Message(message):
    """
        RAG chat message 
        
        message: 是从 @cl.on_message 装饰器接收到的参数，表示用户发送的消息
        msg: msg 用于存储和发送模型生成的回复。
    """
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")    # initial

    class PostMessageHandler(BaseCallbackHandler):
        """
        (这个类不是非必需的, 只是标记能够找到原文档的来源)
        Callback handler for handling the retriever and LLM processes.
        Used to post the sources of the retrieved documents as a Chainlit element.
        """

        def __init__(self, msg: cl.Message):
            BaseCallbackHandler.__init__(self)
            self.msg = msg
            self.sources = set()  # To store unique pairs

        def on_retriever_end(self, documents, *, run_id, parent_run_id, **kwargs):
            for d in documents:
                source_page_pair = (d.metadata['source'], d.metadata['page'])
                self.sources.add(source_page_pair)  # Add unique pairs to the set

        def on_llm_end(self, response, *, run_id, parent_run_id, **kwargs):
            if len(self.sources):
                sources_text = "\n".join([f"{source}#page={page}" for source, page in self.sources])
                self.msg.elements.append(
                    cl.Text(name="Sources", content=sources_text, display="inline")
                )

    async for chunk in runnable.astream(
        message.content,
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler(), PostMessageHandler(msg)]),
    ):
        await msg.stream_token(chunk)

    await msg.send()
    

"""
############################################################################################################
    
                                ==================
                                = Chainlit 装饰器 =   
                                ==================  

    响应的消息传递到 WebUI 上 (新增模型需要添加)

############################################################################################################
"""
@cl.on_message
async def on_message(message: cl.Message):

    model_name = cl.user_session.get("chat_profile")

    if (model_name == 'Qwen2-LC'):
        await LC_Chat_Message(message)

    elif (model_name == "Qwen2"):
        await Chat_Model_Message(message)

    elif (model_name == "Qwen2-RAG"):
        await RAG_Chat_Message(message)
        