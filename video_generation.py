import tempfile
import traceback
import shutil
from io import BytesIO
import os
import numpy as np
import requests
from PIL import Image
from moviepy.editor import (
    ImageClip,
    concatenate_videoclips,
    AudioFileClip,
    concatenate_audioclips,
)
from create_log import create_log
from datetime import datetime
from s3_config import *
import requests


def download(url, save_path):
    response = requests.get(url, stream=True)
    with open(save_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=128):
            file.write(chunk)


def video_generation(params):
    text = (
        '{"@timestamp":"'
        + str(datetime.now())
        + '","log.level":"INFO","app_name":"'
        + os.getenv("APP_NAME")
        + '","app_env":"'
        + os.getenv("APP_ENV")
        + '","message":"start generate video"}'
    )
    create_log(text)
    try:
        user_directory = f"videos/{params.user_id}/{params.vehicle_id}"
        os.makedirs(user_directory, exist_ok=True)
        downloaded_images = []
        for img_url in params.image_urls:
            response = requests.get(img_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                image_pil = Image.open(image_data)
                image_np = np.array(image_pil)
                downloaded_images.append(image_np)
        image_duration = 2
        video_clips = [
            ImageClip(img).set_duration(image_duration) for img in downloaded_images
        ]
        initial_video_clip = concatenate_videoclips(video_clips, method="compose")
        if params.audio_url:
            message = (
                "Video genetrating with audio for user_id :"
                + str(params.user_id)
                + " and vehicle_id :"
                + str(params.vehicle_id)
            )
            text = (
                '{"@timestamp":"'
                + str(datetime.now())
                + '","log.level":"INFO","app_name":"'
                + os.getenv("APP_NAME")
                + '","app_env":"'
                + os.getenv("APP_ENV")
                + '","message":"'
                + message
                + '"}'
            )
            create_log(text)
            download(params.audio_url, str(params.vehicle_id) + ".mp3")
            audio_file = str(params.vehicle_id) + ".mp3"
            audio_clip = AudioFileClip(audio_file)
            num_video_loops = int(audio_clip.duration / initial_video_clip.duration) + 1
            video_clip = concatenate_videoclips(
                [initial_video_clip] * num_video_loops, method="compose"
            )
            num_audio_concatenations = (
                int(video_clip.duration / audio_clip.duration) + 1
            )
            adjusted_audio_clip = concatenate_audioclips(
                [audio_clip] * num_audio_concatenations
            )
            adjusted_audio_clip = adjusted_audio_clip.subclip(0, video_clip.duration)
            video_clip = video_clip.set_audio(adjusted_audio_clip)
        else:
            message = (
                "Video genetrating without audio for user_id :"
                + str(params.user_id)
                + "vehicle_id :"
                + str(params.vehicle_id)
            )
            text = (
                '{"@timestamp":"'
                + str(datetime.now())
                + '","log.level":"INFO","app_name":"'
                + os.getenv("APP_NAME")
                + '","app_env":"'
                + os.getenv("APP_ENV")
                + '","message":"'
                + message
                + '"}'
            )
            create_log(text)
            video_clip = initial_video_clip
        temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        video_clip.write_videofile(
            temp_video_file.name,
            codec="libx264",
            audio_codec="aac",
            fps=1,
            bitrate="5000k",
            threads=4,
            preset="ultrafast",
        )
        s3_bucket = "video-generation"
        s3_key = f"{user_directory}/my_video.mp4"
        s3.upload_file(temp_video_file.name, s3_bucket, s3_key)
        s3_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
        temp_video_file.close()
        if os.path.exists(temp_video_file.name):
            os.remove(temp_video_file.name)
        shutil.rmtree("videos", ignore_errors=True)
        if params.audio_url:
            audio_clip.close()
        if os.path.exists(str(params.vehicle_id) + ".mp3"):
            os.remove(str(params.vehicle_id) + ".mp3")
        message = (
            "Video genetrated successfully for user_id :"
            + str(params.user_id)
            + "vehicle_id : "
            + str(params.vehicle_id)
        )
        text = (
            '{"@timestamp":"'
            + str(datetime.now())
            + '","log.level":"INFO","app_name":"'
            + os.getenv("APP_NAME")
            + '","app_env":"'
            + os.getenv("APP_ENV")
            + '","message":"'
            + message
            + '"}'
        )
        create_log(text)
        # update post log in social
        text = (
            '{"@timestamp":"'
            + str(datetime.now())
            + '","log.level":"INFO","app_name":"'
            + os.getenv("APP_NAME")
            + '","app_env":"'
            + os.getenv("APP_ENV")
            + '","message":"try to do request to social"}'
        )
        create_log(text)

        response = requests.post(
            os.getenv("SOCIAL_API", "http://localhost:82") + "/api/update_post_log",
            data={
                "vehicle_id": params.vehicle_id,
                "user_id": params.user_id,
                "vedio_url": s3_url,
            },
        )
        text = (
            '{"@timestamp":"'
            + str(datetime.now())
            + '","log.level":"INFO","app_name":"'
            + os.getenv("APP_NAME")
            + '","app_env":"'
            + os.getenv("APP_ENV")
            + '","message":"after doing request to social"}'
        )
        create_log(text)

    except Exception as e:
        error_traceback = traceback.format_exc()
        error_trace = str(error_traceback)
        characters_to_replace = ['"', ",", "/", "\\", "\n", "'"]

        # Replacing each character with an empty string
        for char in characters_to_replace:
            error_trace = error_trace.replace(char, " ")

        error_mes = str(e) + error_trace
        text = (
            '{"@timestamp":"'
            + str(datetime.now())
            + '","log.level":"ALERT","app_name":"'
            + os.getenv("APP_NAME")
            + '","app_env":"'
            + os.getenv("APP_ENV")
            + '","USER_id":"'
            + str(params.user_id)
            + '","vehicle_id ":"'
            + str(params.vehicle_id)
            + '","message":"'
            + error_mes
            + '"}'
        )
        create_log(text)
        pass
