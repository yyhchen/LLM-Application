# neo4j 可视化 GraphRAG 生成的知识图谱

---

<br>
<br>


## 📦 Docker & neo4j

首先拉取 `neo4j` 的 image, 这里选择的是 `neo4j-5.22.0` 社区版

```sh
docker pull neo4j:5.22.0-community
```

然后使用 `docker run` 启动 `neo4j`数据库

```sh
docker run -p 7474:7474 -p 7687:7687 --rm --name neo4j-apoc  -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4J_PLUGINS=\[\"apoc\"\] neo4j:5.22.0-community
```


<br>
<br>
<br>


## 📝 导入数据

连接 `neo4j`

```python
from neo4j import GraphDatabase
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "12345678" 
NEO4J_DATABASE = "neo4j"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
```

<br>
<br>

后续导入数据 详情在 [neo4j_display.ipynb](), 导入成功后打开网页即可看到生成的知识图谱

<img src='https://github.com/yyhchen/LLM-Application/blob/main/assets/graphrag_neo4j_display.png'>
