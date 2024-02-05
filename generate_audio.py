from gtts import gTTS
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException
from datetime import datetime
import os
from s3_config import *
import traceback
import shutil
from create_log import create_log


def audio_generation(item, language, output_file):
    try:
        user_directory = f"audio/{item.user_id}/{item.vehicle_id}"
        os.makedirs(user_directory, exist_ok=True)
        audio_path = os.path.join(user_directory, output_file)
        tts = gTTS(item.text, lang=language, tld="us", slow=False)
        tts.save(audio_path)
        try:
            s3.upload_file(
                audio_path,
                "video-generation",
                f"audio/{item.user_id}/{item.vehicle_id}/{output_file}",
            )
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not available")
        os.remove(audio_path)
        shutil.rmtree("audio", ignore_errors=True)
        s3_url = "" #include you s3 url
        text = (
            '{"@timestamp":"'
            + str(datetime.now())
            + '","log.level":"INFO","app_name":"'
            + os.getenv("APP_NAME")
            + '","app_env":"'
            + os.getenv("APP_ENV")
            + '","message":"Audio genetrated successfully for user_id"}'
        )
        create_log(text)
        return {s3_url}
    except Exception as e:
        error_traceback = traceback.format_exc()
        error_trace = str(error_traceback)
        characters_to_replace = ['"', ",", "/", "\\", "\n", "'"]

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
            + str(item.user_id)
            + '","vehicle_id":"'
            + str(item.vehicle_id)
            + '","message":"'
            + error_mes
            + '"}'
        )
        create_log(text)
        pass
