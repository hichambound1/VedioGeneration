from generate_audio import audio_generation
from fastapi import FastAPI, Form ,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from create_log import create_log
import os
from datetime import datetime
from typing import List, Optional
from video_generation import video_generation
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class VideoGenerationParams(BaseModel):
    image_urls: List[str] = Form(...)
    user_id: int = Form(...)
    vehicle_id: int = Form(...)
    audio_url: Optional[str] = Form(None)


class Item(BaseModel):
    text: str
    user_id: int
    vehicle_id: int


@app.get("/monitoring")
def check_status():
    text = (
        '{"@timestamp":"'
        + str(datetime.now())
        + '","log.level":"INFO","app_name":"'
        + os.getenv("APP_NAME")
        + '","app_env":"'
        + os.getenv("APP_ENV")
        + '","message":"Monitoring"}'
    )
    create_log(text)
    return "success"


@app.get("/")
def check_status():
    return "success"


@app.post("/generate_audio")
async def generate_audio(
    item: Item, language: str = "en", output_file: str = "audio.mp3"
):
    res=audio_generation(item, language, output_file)
    return res

@app.post("/generate_video")
async def generate_video(params: VideoGenerationParams,background_tasks: BackgroundTasks):
    background_tasks.add_task(video_generation,params)
    return "proccessed in the background"

if __name__ == "__main__":
    PORT: str = os.getenv("PORT", "8000")
    uvicorn.run(app, host="127.0.0.1", port=int(PORT))
