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
import re


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostRequest(BaseModel):
    post: str

def get_tweet_text(tweet_id: str) -> str:
    token = os.getenv("X_BEARER_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.twitter.com/2/tweets/{tweet_id}?tweet.fields=text"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["text"]
    else:
        return ""

@app.post("/score")
async def score_post(data: PostRequest):
    try:
        post_content = data.post.strip()

        # URLならID抽出してツイート取得
        match = re.search(r"status/(\d+)", post_content)
        if match:
            tweet_id = match.group(1)
            tweet_text = get_tweet_text(tweet_id)
            if not tweet_text:
                return {"analysis": "申し訳ありませんが、そのリンクを開くことができません。投稿の内容を直接教えていただければ、辛口評価をお届けします。"}
        else:
            tweet_text = post_content

        with open("prompt_template.txt", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{post}", tweet_text)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはSNS投稿の辛口評論家で、やや皮肉屋です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
        )
        analysis = response.choices[0].message.content
        print("✅ 投稿取得成功:", tweet_text)
        return {"analysis": analysis}

    except Exception as e:
        print("OpenAI API Error:", e)
        return {"error": str(e)}


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

