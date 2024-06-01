"""
    源自清华大学 github 网站上的案例（https://github.com/THUDM/ChatGLM-6B）

    调试量化 int4级别

    先保证本地安装调试完CUDA，然后创建conda 环境 进行环境配置 pip install -r requirements.txt -i https://mirror.sjtu.edu.cn/pypi/web/simple

"""


from transformers import AutoTokenizer, AutoModel

model_path = "D:\CodeLibrary\ChatGLM\chatglm26b"

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
# model = AutoModel.from_pretrained(model_path, trust_remote_code=True, device='cuda')
# 按需修改，目前只支持 4/8 bit 量化
model = AutoModel.from_pretrained(model_path, trust_remote_code=True).quantize(4).half().cuda()
model = model.eval()

response, history = model.chat(tokenizer, "你好", history=[])
print(response)

response, history = model.chat(tokenizer, "晚上睡不着应该怎么办", history=history)
print(response)

