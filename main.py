import os
from moviepy.editor import *
from gtts import gTTS
from pydub import AudioSegment

# フォルダのパス
text_folder = "text_folder"
bgm_folder = "bgm_folder"
background_folder = "background_folder"
output_folder = "output_folder"

# フォルダが存在しない場合は作成
os.makedirs(output_folder, exist_ok=True)

# 一時ファイルのリスト
temp_files = []

# 読み聞かせの速度 (1.0 が通常速度)
speed_factor = 1.0

# テキストファイルの読み込み
for text_file in os.listdir(text_folder):
    if text_file.endswith(".txt"):
        text_path = os.path.join(text_folder, text_file)
        with open(text_path, "r", encoding="utf-8") as file:
            text_content = file.read()

        # テキストから音声を生成
        tts = gTTS(text=text_content, lang='ja')
        speech_mp3 = "speech.mp3"
        tts.save(speech_mp3)
        temp_files.append(speech_mp3)

        # スピーチの読み込み
        speech_audio = AudioFileClip(speech_mp3)

        # スピーチの速度を調整
        adjusted_speech_audio = speech_audio.fx(vfx.speedx, speed_factor)
        adjusted_speech_mp3 = "adjusted_speech.mp3"
        adjusted_speech_audio.write_audiofile(adjusted_speech_mp3, codec='mp3')
        temp_files.append(adjusted_speech_mp3)

        # 調整後のスピーチの長さを取得
        speech_duration = adjusted_speech_audio.duration

        # BGMの読み込みと合成
        for bgm_file in os.listdir(bgm_folder):
            if bgm_file.endswith(".mp3"):
                bgm_path = os.path.join(bgm_folder, bgm_file)
                bgm = AudioSegment.from_mp3(bgm_path)

                # BGMをスピーチの長さに合わせて繰り返し
                loops_needed = int(speech_duration / bgm.duration_seconds) + 1
                bgm_extended = bgm * loops_needed
                bgm_extended = bgm_extended[:int(speech_duration * 1000)]  # スピーチと同じ長さにカット

                speech = AudioSegment.from_mp3(adjusted_speech_mp3)
                combined = bgm_extended.overlay(speech)
                combined_audio = "combined_audio.mp3"
                combined.export(combined_audio, format="mp3")
                temp_files.append(combined_audio)

                # 背景画像の読み込み
                for background_file in os.listdir(background_folder):
                    if background_file.endswith(".png"):
                        background_path = os.path.join(background_folder, background_file)
                        background = ImageClip(background_path).set_duration(speech_duration)

                        # 音声と背景画像を合成して動画を作成
                        audio = AudioFileClip(combined_audio)
                        video = background.set_audio(audio)
                        output_path = os.path.join(output_folder, f"{os.path.splitext(text_file)[0]}_{os.path.splitext(bgm_file)[0]}_{os.path.splitext(background_file)[0]}.mp4")
                        video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

# 一時ファイルの削除
for temp_file in temp_files:
    if os.path.exists(temp_file):
        os.remove(temp_file)
