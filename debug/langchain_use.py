from langchain import PromptTemplate, LLMChain
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain import HuggingFacePipeline

model_path = "D:\CodeLibrary\ChatGLM\chatglm2-6b_model"

if torch.cuda.is_available():
    print(torch.cuda.device_count())
    device = torch.device('cuda:0' if torch.cuda.is_available() else "cpu")
    print(device)
else:
    print('没有GPU')
    device = torch.device('cpu')

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True).half().to(device)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=512,
    top_p=1,
    repetition_penalty=1.15,
    device=0 if torch.cuda.is_available() else -1  # Ensure the pipeline uses the correct device
)
glm_model = HuggingFacePipeline(pipeline=pipe)

template = '''
#context# 
You are a good helpful, respectful and honest assistant.You are ready for answering human's question and always answer as helpfully as possible, while being safe.
Please ensure that your responses are socially unbiased and positive in nature. 
#question# 
Human:What is a good name for a company that makes {product}?"
'''
prompt = PromptTemplate(
    input_variables=["product"],
    template=template
)
chain = LLMChain(llm=glm_model, prompt=prompt)

product = "running shoes"
input_data = prompt.format(product=product)
input_data = tokenizer(input_data, return_tensors='pt').input_ids.to(device)  # Move input data to the correct device

result = chain.run(product)
print(result)
