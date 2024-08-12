from fastapi import FastAPI
from chainlit.utils import mount_chainlit

app = FastAPI()


@app.get("/app")
def read_main():
    return {"message": "Hello World from main app"}

mount_chainlit(app=app, target="my_cl_app.py", path="/chainlit")
