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




