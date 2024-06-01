from transformers import AutoTokenizer, AutoModel

model_path = "D:\CodeLibrary\Pycharm\chatglm2-6b_model"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

# 初始化或加载历史对话
history = []


def save_history(filename, history):
    with open(filename, 'w', encoding="utf-8") as f:
        for line in history:
            f.write(str(line) + '\n')



def load_history(filename):
    history = []
    try:
        with open(filename, 'r', encoding="utf-8") as f:
            for line in f:
                history.append(line.strip())
    except FileNotFoundError:
        pass
    return history


history = load_history('conversation_history.txt')

model = AutoModel.from_pretrained(model_path, trust_remote_code=True).quantize(4).half().cuda()
model = model.eval()

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    response, history = model.chat(tokenizer, user_input, history=history)
    print("AI:", response)

    # 保存对话历史
    save_history('conversation_history.txt', history)
