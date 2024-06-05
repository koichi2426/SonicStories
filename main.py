import os
import re
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
from io import BytesIO
from moviepy.editor import *
from gtts import gTTS
from pydub import AudioSegment

# ノイズを削除する関数
def remove_noise(text):
    noise_chars = r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?~`]'
    cleaned_text = re.sub(noise_chars, '', text)
    return cleaned_text

# Stable Diffusionを使用して画像を生成する関数
def generate_image_from_text(prompt, output_path):
    model_id = "CompVis/stable-diffusion-v1-4"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipe = StableDiffusionPipeline.from_pretrained(model_id)
    pipe = pipe.to(device)

    image = pipe(prompt).images[0]
    image.save(output_path)

# create_video_from_text関数の定義
def create_video_from_text(text_content, bgm_path, background_path, output_path, speech_speed=1.0):
    if not text_content.strip():
        print("Warning: The provided text is empty. Skipping video creation.")
        return
    
    temp_files = []

    tts = gTTS(text=text_content, lang='ja')
    speech_mp3 = "speech.mp3"
    tts.save(speech_mp3)
    temp_files.append(speech_mp3)

    speech = AudioSegment.from_mp3(speech_mp3)
    adjusted_speed_speech = speech._spawn(speech.raw_data, overrides={
        "frame_rate": int(speech.frame_rate * speech_speed)
    }).set_frame_rate(speech.frame_rate)
    adjusted_speed_speech_mp3 = "adjusted_speed_speech.mp3"
    adjusted_speed_speech.export(adjusted_speed_speech_mp3, format="mp3")
    temp_files.append(adjusted_speed_speech_mp3)

    speech_duration = adjusted_speed_speech.duration_seconds

    bgm = AudioSegment.from_mp3(bgm_path)

    loops_needed = int(speech_duration / bgm.duration_seconds) + 1
    bgm_extended = bgm * loops_needed
    bgm_extended = bgm_extended[:int(speech_duration * 1000)]

    combined = bgm_extended.overlay(adjusted_speed_speech)
    combined_audio = "combined_audio.mp3"
    combined.export(combined_audio, format="mp3")
    temp_files.append(combined_audio)

    background = ImageClip(background_path).set_duration(speech_duration)

    audio = AudioFileClip(combined_audio)
    video = background.set_audio(audio)
    video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def get_chapters(filename):
    chapters = []
    with open(filename, 'r', encoding='utf-8') as file:
        chapter_text = ''
        for line in file:
            line = line.strip()
            if line == "%%%%%%%%":
                chapters.append(chapter_text)
                chapter_text = ''
            else:
                chapter_text += line + '\n'
        chapters.append(chapter_text)
    return chapters

def concatenate_videos(output_folder, final_output):
    video_files = [f for f in os.listdir(output_folder) if f.endswith('.mp4')]
    video_files.sort()

    clips = [VideoFileClip(os.path.join(output_folder, file)) for file in video_files]
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(final_output, codec="libx264", audio_codec="aac")

# 使用例
chapters = get_chapters('text_folder/text.txt')
bgm_folder = 'bgm_folder'
background_folder = 'background_folder'
output_folder = 'output_folder'

bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith('.mp3')]
if bgm_files:
    bgm_file = os.path.join(bgm_folder, bgm_files[0])
    for i in range(0, len(chapters), 2):
        chapter_text = ''.join(chapters[i:i+2])
        chapter_text = remove_noise(chapter_text)
        output_file = os.path.join(output_folder, f'{i//2 + 1}.mp4')

        background_file = os.path.join(background_folder, f'{(i//2)+1}.png')
        generate_image_from_text(chapter_text, background_file)

        create_video_from_text(chapter_text, bgm_file, background_file, output_file)

    final_output_file = os.path.join(output_folder, 'story.mp4')
    concatenate_videos(output_folder, final_output_file)

    print("All videos created and concatenated successfully.")
else:
    print("No BGM files found in the bgm_folder.")
