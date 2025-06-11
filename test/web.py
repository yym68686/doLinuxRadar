from seleniumbase import SB
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    url: str

app = FastAPI()

def get_linux_do_content(url: str):
    with SB(test=True, uc=True, headless=True) as sb:
        sb.open(url)
        text = sb.get_text("body > pre")
        return text

@app.post("/get_content/")
async def read_item(item: Item):
    content = get_linux_do_content(item.url)
    return {"content": content}

# print(get_linux_do_content())