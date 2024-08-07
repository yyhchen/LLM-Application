# GraphRAG experiments report

---


## 📦 environments

[data](/GraphRAG/input/)：摘选自 [Tencent Research Institute](https://www.tisi.org/) 的最新十篇研究报告


<br>
<br>


## 🚀 experiments details


### API

先启动服务, 方便后面统计资源消耗, 我们可以看到启动 `Qwen2-7B-Instruct` 和 `bge-m3` 消耗的显存为 20G左右:

![gpu consume](/assets/graphrag_memoryconsume.png)


<br>
<br>


### GraphRAG WorkSpace
执行完 `python -m graphrag.index --init --root ` 命令后，出现了 `.env`, `settings.yaml`, `output`文件夹, `prompts`文件夹

如下图所示:

![graphrag_detail1](/assets/graphrag_detail1.png)


我们会发现, `prompts` 文件夹中还有四个文件:

1. claim_extraction.txt
2. community_report.txt
3. entity_extraction.txt
4. summarize_descriptions.txt

这四个文件是关于如何提取claim, entity, 以及做些摘要任务为后续构建知识图谱做准备。（后续需要详细的研究报告）

<br>

接下来是构建知识图谱的环节:

![](/assets/graphrag_kg_construction1.png)

我们可以看到 `chunk` 的大小是 1200，分成了 145 份, `chunk` 的大小可以在 `settings.yaml` 中设置，这里我们使用的是默认的数值。

**在第一阶段的 `Verb entity_extract` 中，并没有使用到GPU，因为显存的大小没有发生变化**

> 注意：本次文档资料约7w1k多字, 第一次 indexing 的过程花了 70 分钟左右（奇怪的是发生错误后再indexing并不需要这么长时间）. 并且在 `create_base_entity_graph` 出现了错误，如下图所示:

![create_base_entity_graph](/assets/graphrag_error1.png)

日志显示的详细错误如下:

![create_base_entity_graph  error detail](/assets/grapgrag_error2.png)

在构建 `entity_graph` 时出现了错误，结合 [issue](https://github.com/microsoft/graphrag/issues/443) 猜测 可能是模型能力不够，导致无法解析成想要的格式 (**很大可能会随着数据量的增加出现类似的问题**) 


> 目前发现，只要在一个容器内启动过 graphrag，再次 indexing数据一定会出现这个bug！！！暂时不懂这是为什么，跟模型规模貌似不是直接关系


