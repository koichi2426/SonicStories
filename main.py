import os
from moviepy.editor import *
from gtts import gTTS
from pydub import AudioSegment
import re

# ノイズを削除する関数
def remove_noise(text):
    # ノイズとして定義された記号を削除
    noise_chars = r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?~`]'
    cleaned_text = re.sub(noise_chars, '', text)
    return cleaned_text

# create_video_from_text関数の定義
def create_video_from_text(text_content, bgm_path, background_path, output_path, speech_speed=1.0):
    if not text_content.strip():
        print("Warning: The provided text is empty. Skipping video creation.")
        return
    
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

# テキストファイルから章ごとに文字列を取得する関数
def get_chapters(filename):
    chapters = []  # 章ごとの文字列を格納するリスト

    if not os.path.exists(filename):
        print(f"Error: The file {filename} does not exist.")
        return chapters  # 空のリストを返す

    with open(filename, 'r', encoding='utf-8') as file:
        chapter_text = ''  # 現在の章の文字列を初期化する
        for line in file:
            line = line.strip()  # 行末の改行を削除

            if line == "%%%%%%%%":
                # `%%%%%%%%`で章が終わるとき、現在の章をリストに追加して新しい章のための文字列を初期化する
                chapters.append(chapter_text)
                chapter_text = ''  # 新しい章のために初期化
            else:
                # 現在の章の文字列に行を追加する
                chapter_text += line + '\n'

        # 最後の章をリストに追加する
        chapters.append(chapter_text)

    return chapters

# output_folderにあるMP4ファイルを取得し、順番に連結する
def concatenate_videos(output_folder, final_output):
    video_files = [f for f in os.listdir(output_folder) if f.endswith('.mp4')]
    video_files.sort()  # ファイル名でソートして順番に連結する

    # VideoFileClipオブジェクトのリストを作成
    clips = [VideoFileClip(os.path.join(output_folder, file)) for file in video_files]

    # 動画を連結
    final_clip = concatenate_videoclips(clips, method="compose")

    # 最終出力ファイルを保存
    final_clip.write_videofile(final_output, codec="libx264", audio_codec="aac")

# 使用例

# ディレクトリが存在しない場合は作成
text_folder = 'text_folder'
bgm_folder = 'bgm_folder'
background_folder = 'background_folder'
output_folder = 'output_folder'
chapters_folder = 'chapters_folder'

os.makedirs(text_folder, exist_ok=True)
os.makedirs(bgm_folder, exist_ok=True)
os.makedirs(background_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)
os.makedirs(chapters_folder, exist_ok=True)

# テキストファイルから章ごとの文字列を取得
story_file = os.path.join(text_folder, 'story.txt')
chapters = get_chapters(story_file)

if not chapters:
    print(f"No chapters found in {story_file}. Please check the file.")
else:
    # BGMフォルダ内の最初のmp3ファイルを取得
    bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith('.mp3')]
    if bgm_files:
        # BGMフォルダ内の最初のmp3ファイルを取得
        bgm_file = os.path.join(bgm_folder, bgm_files[0])

        # 2章ごとにビデオを生成
        for i in range(0, len(chapters), 2):
            chapter_text = ''.join(chapters[i:i+2])  # 2章ずつのテキストを取得し、連結して単一の文字列にする
            chapter_text = remove_noise(chapter_text)  # ノイズを削除

            if chapter_text.strip():  # chapter_textが空でない場合に実行
                # prompt_textを作成
                prompt_text = chapter_text + " この場面に適した画像をアニメ調で幻想的に１つ生成してください。"
                
                # 章ごとにテキストファイルを保存
                chapter_file = os.path.join(chapters_folder, f'chapter{i//2 + 1}.txt')
                with open(chapter_file, 'w', encoding='utf-8') as file:
                    file.write(prompt_text)
                
                output_file = os.path.join(output_folder, f'{i//2 + 1}.mp4')  # 出力ファイル名

                # BGMファイルと背景画像ファイルのパス
                background_file = os.path.join(background_folder, f'{(i//2)+1}.png')

                # ターミナルにメッセージを表示して処理を停止
                print(f"最新のチャプターのサムネイルをbackground_folderに配置してください: {background_file}")
                input("ターミナルをクリックして続行...")

                # create_video_from_text関数を呼び出してビデオを生成
                create_video_from_text(chapter_text, bgm_file, background_file, output_file)

        # すべてのビデオを連結して最終出力ファイルを作成
        final_output_file = os.path.join(output_folder, 'story.mp4')
        concatenate_videos(output_folder, final_output_file)

        print("All videos created and concatenated successfully.")
    else:
        print("No BGM files found in the bgm_folder.")
