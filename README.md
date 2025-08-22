# LLM

基于主流大模型做一些应用, 集成了 RAG, GraphRAG, Agent, 文生图, 多模态对话等

---


## 📦 environments

```bash
cd Chainlit && pip install -r requirements.txt
```

<br>

在 Chainlit 目录下，执行:

```bash
chainlit run multi_chat.py
```
效果如下图所示：

![使用界面](/assets/multi_chat1.png)

目前已有的功能是 RAG, GraphRAG, Agent, 文生图, 多模态对话等

![功能](/assets/multi_chat1.gif)

在图文对话过程，考虑到不是纯语言模型的能力，实现了**非图对话**的判断：
![发图问答](/assets/multi_chat2.gif)


<br>
<br>
<br>



## 🛠 各种技术的示范案例

### [langchain_QA](https://github.com/yyhchen/LLM-Application/tree/main/langchain_QA)

基于chatglm2-6b + langchain + chroma 做技术知识库问答(RAG)      
- [本地知识库来源](https://github.com/yyhchen/Notes/tree/main/NLP%20review)


基于Qwen2-0.5B-Instruct 提升 RAG 做法律知识问答
- [知识来源](https://huggingface.co/datasets/cfa532/CHLAWS)


<br>
<br>


### [GraphRAG](https://github.com/yyhchen/LLM-Application/tree/main/GraphRAG)

基于[官方GraphRAG](https://microsoft.github.io/graphrag/posts/get_started/)做的简单演示，并使用 `neo4j` 可视化知识图谱；演示的数据使用的是[text.txt](https://github.com/yyhchen/LLM-Application/blob/main/GraphRAG/text.txt) 


<br>
<br>


### [AutoGen](https://github.com/yyhchen/LLM-Application/tree/main/AutoGen)

基于[官方AutoGen](https://microsoft.github.io/autogen/docs/Getting-Started)编写的一个案例实现 [Customize Speak Seletion](https://microsoft.github.io/autogen/docs/topics/groupchat/customized_speaker_selection) （实际上就是一个多轮的 multi-agent, 根据不同任务进行 agent选择）


<br>
<br>


### [AI 早报](https://github.com/yyhchen/LLM-Application/tree/main/app%20case)

通过爬取[aibase](https://news.aibase.com/zh/news) 制作ai早报

- [ai_information_daily.ipynb]() 和 [ai_daily_news.py]() 包括了爬取的代码和生成摘要的代码，两者是一样的
- [reading.html]()  是方便读取新闻的网页，做了卡片视觉效果，效果截图如下：

![功能](/assets/ai_info_show.gif.gif)


更多其他案例后续持续更新