import gradio as gr
from langchain.llms.base import LLM
from typing import Any, List, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain.chains import RetrievalQA
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_core.prompts import PromptTemplate
import torch
import os
import warnings
from transformers import AutoTokenizer, AutoModelForCausalLM
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# 前置环境
device = "cuda"
llm_model_path = '/root/private_data/models/Qwen/Qwen2-0.5B-Instruct'

tokenizer = AutoTokenizer.from_pretrained(llm_model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(llm_model_path, trust_remote_code=True).to(device)

# 定义模型
class Qwen2_LLM(LLM):
    def __init__(self):
        super().__init__()

    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None) -> str:
        message = [
            {"role": "system", "content": "you are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        
        text = tokenizer.apply_chat_template(
            conversation=message, 
            tokenize=False, 
            add_generation_prompt=True
        )

        model_inputs = tokenizer(text, return_tensors="pt").to(device)

        generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=512, do_sample=True)

        # 因为会根据 所有的模板内容进行 generation， 所以要去掉前面的（每一次输入的）模板
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]

        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return response

    @property
    def _llm_type(self) -> str:
        return "Qwen2-1.5B"

# 加载数据
dataset_path = '/root/private_data/models/cfa532/CHLAWS'
loader = DirectoryLoader(dataset_path, glob='laws4.txt')
documents = loader.load()

child_spliter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300)
parent_spliter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)

embed_model_path = '/root/private_data/models/BAAI/bge-m3'
embeddings = HuggingFaceBgeEmbeddings(model_name=embed_model_path)

persist_directory = 'chroma_data'
vectorstore = Chroma(collection_name="laws_document", embedding_function=embeddings, persist_directory=persist_directory)
store = InMemoryStore()
retriever = ParentDocumentRetriever(vectorstore=vectorstore, docstore=store, child_splitter=child_spliter, parent_splitter=parent_spliter)
retriever.add_documents(documents, id=None)

qwen = Qwen2_LLM()
template = """
基于以下信息来回答用户问题。如果你不知道答案，就说你不知道，不要试图编造答案。尽量使答案简单，并最后回答的最后说“谢谢你的提问！”。                      
已知信息： 
{context} 
问题：
{question}
"""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])

chain_type_kwargs = {"prompt": prompt}

qa = RetrievalQA.from_chain_type(
    llm=qwen, 
    chain_type="stuff", 
    retriever=retriever, 
    chain_type_kwargs=chain_type_kwargs,
    return_source_documents=True
)

def query_qa(query):
    result = qa.invoke({"query": query})
    return result['result']

def stream_query_qa(query, history):
    partial_message = ""
    result = qa.invoke({"query": query})
    for token in result['result']:
        partial_message += token
        yield partial_message

# 构建 Gradio 界面
gr.ChatInterface(
    stream_query_qa,
    chatbot=gr.Chatbot(height=300),
    textbox=gr.Textbox(placeholder="Chat with me!", container=False, scale=7),
    description="This is the demo for Gradio UI consuming TGI endpoint with huggingface🤗 model.",
    title="Qwen 🇨🇳 vLLM 🚀",
    examples=["你是谁?", "你能干什么？", "请你介绍下北京"],
    retry_btn="Retry",
    undo_btn="Undo",
    clear_btn="Clear",
).queue().launch(server_name="0.0.0.0", share=False)
