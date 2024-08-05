# AutoGen

本地LLM部署 + AutoGen

- [AutoGen Getting-Started](https://microsoft.github.io/autogen/docs/Getting-Started)

- [paper](https://arxiv.org/abs/2308.08155)

---

<br>
<br>


## 📖 Introduction

AutoGen 是一个用于构建和训练基于大型语言模型（LLM）的对话代理的框架。它允许用户通过定义一组任务和一组代理来构建一个对话系统，并使用 LLM 来训练代理之间的交互，以实现特定的任务目标。

<img src='https://github.com/yyhchen/LLM-Application/blob/main/assets/autogen_intro.png'>


<br>
<br>


## 📦 environments
python >=3.8 & <3.13

安装 `AutoGen`
```sh
pip install pyautogen
```


<br>
<br>
<br>


## 🔨 One of demo Guide

<img src="https://github.com/yyhchen/LLM-Application/blob/main/assets/autogen_speaker.png">

构建一个简单的 StateFlow 模型，定制一个 Speaker，定义如下 Agent：
- Initializer：发送任务启动工作流程
- Coder：编写代码从 互联网检索论文（这个是真可以～）
- Executor：执行代码
- Scientist：阅读论文并写总结

<br>

### API

先启动 API, 运行 [openai_api.sh](https://github.com/yyhchen/LLM-Application/tree/main/AutoGen/openai_api.sh):

```sh
bash openai_api.sh
```

<br>

### AutoGen案例

[autogen.ipynb](https://github.com/yyhchen/LLM-Application/tree/main/AutoGen/autogen.ipynb) 改编自 [AutoGen官网案例](https://microsoft.github.io/autogen/docs/topics/groupchat/customized_speaker_selection) 


<br>
<br>


## 🔍 RAG in AutoGen 

AutoGen 支持 RAG，通过在 LLM 的输入中添加来自外部数据源的文本片段，以增强模型的生成能力。

<br>

### envs
```bash
# 加 -q 控制台没有安装信息
pip install pyautogen[retrievechat] langchain "chromadb<0.4.15" -q
```

<br>


### 案例

[autogen_rag.ipynb](https://github.com/yyhchen/LLM-Application/tree/main/AutoGen/autogen_rag.ipynb)