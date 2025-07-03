from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
import requests


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# ★ CORS設定（全てのオリジンから許可 → 必要に応じて限定可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ここを ["http://127.0.0.1:5500"] などに限定することも可能
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostRequest(BaseModel):
    post: str

@app.post("/score")
async def score_post(data: PostRequest):
    try:
        with open("prompt_template.txt", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{post}", data.post)

        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-3.5-turbo, gpt-4o, 
            messages=[
                {"role": "system", "content": "あなたはSNS投稿の辛口評論家で、やや皮肉屋です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
        )
        return {"analysis": response.choices[0].message.content}

    except Exception as e:
        print("OpenAI API Error:", e)
        return {"error": str(e)}


def get_tweet_text(tweet_id: str) -> str:
    token = os.getenv("X_BEARER_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.twitter.com/2/tweets/{tweet_id}?tweet.fields=text"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["text"]
    else:
        return "ツイートの取得に失敗しました"
