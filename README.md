# LLM

基于主流大模型做一些应用

---


## [langchain_QA](https://github.com/yyhchen/LLM-Application/tree/main/langchain_QA)

基于chatglm2-6b + langchain + chroma 做技术知识库问答(RAG)      
- [本地知识库来源](https://github.com/yyhchen/Notes/tree/main/NLP%20review)


基于Qwen2-0.5B-Instruct 提升 RAG 做法律知识问答
- [知识来源](https://huggingface.co/datasets/cfa532/CHLAWS)


<br>
<br>


## [GraphRAG](https://github.com/yyhchen/LLM-Application/tree/main/GraphRAG)

基于[官方GraphRAG](https://microsoft.github.io/graphrag/posts/get_started/)做的简单演示，并使用 `neo4j` 可视化知识图谱；演示的数据使用的是[text.txt](https://github.com/yyhchen/LLM-Application/blob/main/GraphRAG/text.txt) 


<br>
<br>


## [AutoGen](https://github.com/yyhchen/LLM-Application/tree/main/AutoGen)

基于[官方AutoGen](https://microsoft.github.io/autogen/docs/Getting-Started)编写的一个案例实现 [Customize Speak Seletion](https://microsoft.github.io/autogen/docs/topics/groupchat/customized_speaker_selection) （实际上就是一个多轮的 multi-agent, 根据不同任务进行 agent选择）