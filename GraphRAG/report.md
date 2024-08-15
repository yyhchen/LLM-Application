# GraphRAG experiments report

---


## 📦 environments

[data](/GraphRAG/input/)：摘选自 [Tencent Research Institute](https://www.tisi.org/) 的最新十篇研究报告

<br>

三个独立的环境 (建议用 `python -v venv xxx`):

- graphrag
- embeddings model
- LLM model


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


<br>


`indexing` 成功提取数据后的结果（重新开的容器全部重新开始运行的）如下图所示：

![indexing result](/assets/graphrag_indexing_result.png)


<br>
<br>
<br>

### Command Line Query

- global search
- local search


#### 1. global search

```bash
python -m graphrag.query --root ./ragtest --method global "国企数字化转型面临的挑战有哪些？"
```


结果如下图所示：
![global search result](/assets/graphrag_global_result.png)]


<br>


#### 2. local search

```bash
python -m graphrag.query --root ./ragtest --method local "国企数字化转型面临的挑战有哪些？"
```

结果如下图所示：

![local search result](/assets/graphrag_local_result.png)



<br>
<br>
<br>



### Notebook Query

- global search
- local search


#### 1. global search

[global_search.ipynb](/GraphRAG/notebook/global_search.ipynb)

运行部分结果如下图所示：



<br>


#### 2. local search

[local_search.ipynb](/GraphRAG/notebook/local_search.ipynb)


运行部分结果如下图所示：




<br>
<br>
<br>


执行 查询后， 会在项目文件同级上产生一个 `lancedb` 文件夹，貌似放的是查询的数据, 如下图所示：







<br>
<br>
<br>



## 🪫 Extra


### 部署优化 (超参数，非算子类优化)

> 量化

利用 `vLLM` 部署本地模型的时候，`Qwen2-72B-Instruct` A800-80G 单卡，可以考虑用 `int8` 精度，这样单卡可以使用

<br>

> 加速

小模型加速可以使用更大的缓存 部署 API 时加大 `--gpu-memory-utilization` 的数值（默认是0.9， 我实验用的0.3），但是这里要考虑显存的问题。加大缓存可以使得 indexing builder 加速

<br>

> 分布式（多卡）

启动部署 API 的时候，加上参数 `--tensor-parallel-size 2` 使用双卡部署，`Qwen2-72B-Instruct`部署 `FP16` 推荐的是两张 A800-80G


<br>
<br>


### GraphRAG 优化 (通过 settings.yaml 等文件配置，非源码优化)


> prompts/entity_extraction.txt

精简 `entity_extraction.txt` 的prompts内容,减少 LLM 输入的 tokens 数量（但不容易尝试, 也可能会降低精度等问题）

<br>


> 增加 `chunk` 大小

在 `settings.yaml` 中增加 `chunk` 大小，默认是 1200, `overlap` 默认是 100。

```yaml
chunks:
  size: 1200
  overlap: 100
  group_by_columns: [id]
```


<br>
<br>
<br>



## ❌ 错误总结

### 多卡vLLM部署出现的问题

双卡部署 `Qwen2-72B-Instruct` 很大概率出现下面错误：
```shell
vllm.engine.async_llm_engine.AsyncEngineDeadError: Background loop has errored already
```

以上错误可通过vLLM终端日志查看, 可能原因是请求量太大和需要的吞吐量太大处理不了，也可能是 显存不够 (未验证 [issue](https://github.com/vllm-project/vllm/issues/5060)) 


我的启动配置是:
```bash
python -m vllm.entrypoints.openai.api_server --model /root/private_data/models/Qwen/Qwen2-72B-Instruct --served-model-name Qwen2-72B-Instruct --max-model-len 14336 --gpu-memory-utilization 0.98 --tensor-parallel-size 2 

```

> 吞吐量：5~6 token/s, 非常慢～

**可能的解决方法：** 重启多几次有几率成功


<br>
<br>
<br>



### 最后创建 create_final_communities_report.parquet 文件出现问题

可能是报显存或者 吞吐量太低导致的。




<br>
<br>
<br>



# 细节分析

## 根据 《霸王别姬》 做 GraphRAG 详细报告分析

> ‼️ 前提：GraphRAG的查询分为`global-search` 和 `local-search`。
>
> `global-search` 方法通过以 map-reduce 方式搜索所有 A生成的社区报告来生成答案。这是一种资源密集型方法，需要LLM支持的context window足够大，最好是32K的模型，但通常可以很好地回答需要了解整个数据集的问题。
>
> `local-search` 方法通过将AI 提取到知识图谱中的相关数据与原始文档的文本块相结合来生成答案，此方法适用于需要了解文档中提到的特定实体的问题



<br>

这里模仿官方的例子写了两个问题来分别进行 `local-search` 和 `global-search`:

1. `local-search`: "谁是程蝶衣？他的主要关系是什么？"
2. `global-search`: "这篇小说讲了一个什么故事？"


<br>
<br>

### ⌨️ 使用 CLI 命令行进行查询

> global search

```
python -m graphrag.query --root . --method global "这篇小说讲了一个什么故事？"
```

结果如下图所示：

![global search result](/assets/concubine_global_search.png)



<br>
<br>

> local search

```
python -m graphrag.query --root . --method local "谁是程蝶衣？他的主要关系是什么？"
```

结果如下图所示：

![local search result](/assets/concubine_local_search.png)


<br>


结论: 可以看到效果还是很不错的。



<br>
<br>


### 🏞 结合 chainlit + graphrag-server 做 webui 查询

首先是 `local search`：

![graphrag server local search](/assets/concubine_server_local_search.png)


完全没效果，看了下日志：

![server local log](/assets/concubine_server_local_search_log.png)

我猜测可能的原因是，`graphrag-server` 中 对 `local.search` 的实现有bug，因为在 `neo4j` 的 `_entity_` 里面确实也没看到 `程蝶衣` 这个实体，`程蝶衣` 是 `组织`标签里, 如下图所示。 但奇怪的是为什么官方的 CLI 却能只找到答案呢？

![neo4j entity](/assets/concubine_neo4j_entity_1.png)


奇怪的是，发现了大类 `_entity_` 也包含了 `程蝶衣` ,如下图:

![neo4j entity2](/assets/concubine_neo4j_entity_2.png)


那么，还是回到刚刚，bug 在 `graph-server` 处理 `local-search` 的代码里面.


<br>


接下来是 `global search`:`

![graphrag server global search](/assets/concubine_server_global_search.png)


可以看到 `global search` 在 `graphrag-server` 代码中还是没有失效的，我们还可以从 日志 中证明这一点，日志部分节选如下图所示.

![server global log1](/assets/concubine_server_global_search_log1.png)

![server global log2](/assets/concubine_server_global_search_log2.png)


我们还可以从日志中获取的信息是，答案确实是 通过 `map-reduce` 的方式进行搜索，然后通过模型总结生成答案的。