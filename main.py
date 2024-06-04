import os
from moviepy.editor import *
from gtts import gTTS
from pydub import AudioSegment

def create_video_from_text(text_content, bgm_path, background_path, output_path, speech_speed=1.0):
    # 一時ファイルのリスト
    temp_files = []

    # テキストから音声を生成
    tts = gTTS(text=text_content, lang='ja')
    speech_mp3 = "speech.mp3"
    tts.save(speech_mp3)
    temp_files.append(speech_mp3)

    # 読み上げ速度を調整
    speech = AudioSegment.from_mp3(speech_mp3)
    adjusted_speed_speech = speech._spawn(speech.raw_data, overrides={
        "frame_rate": int(speech.frame_rate * speech_speed)
    }).set_frame_rate(speech.frame_rate)
    adjusted_speed_speech_mp3 = "adjusted_speed_speech.mp3"
    adjusted_speed_speech.export(adjusted_speed_speech_mp3, format="mp3")
    temp_files.append(adjusted_speed_speech_mp3)

    # 調整後のスピーチの長さを取得
    speech_duration = adjusted_speed_speech.duration_seconds

    # BGMの読み込みと合成
    bgm = AudioSegment.from_mp3(bgm_path)

    # BGMをスピーチの長さに合わせて繰り返し
    loops_needed = int(speech_duration / bgm.duration_seconds) + 1
    bgm_extended = bgm * loops_needed
    bgm_extended = bgm_extended[:int(speech_duration * 1000)]  # スピーチと同じ長さにカット

    combined = bgm_extended.overlay(adjusted_speed_speech)
    combined_audio = "combined_audio.mp3"
    combined.export(combined_audio, format="mp3")
    temp_files.append(combined_audio)

    # 背景画像の読み込み
    background = ImageClip(background_path).set_duration(speech_duration)

    # 音声と背景画像を合成して動画を作成
    audio = AudioFileClip(combined_audio)
    video = background.set_audio(audio)
    video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

    # 一時ファイルの削除
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
# 使用例
text_content = "ここにテキストを入力してください。"
bgm_file = "bgm_folder/216_long_BPM65.mp3"
background_file = "background_folder/2.png"
output_file = "output_folder/output_video1.mp4"

create_video_from_text(text_content, bgm_file, background_file, output_file)