import os
from moviepy.editor import *
from gtts import gTTS
from pydub import AudioSegment

# create_video_from_text関数の定義
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

# テキストファイルから章ごとに文字列を取得する関数
def get_chapters(filename):
    chapters = []  # 章ごとの文字列を格納するリスト

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

# テキストファイルから章ごとの文字列を取得
chapters = get_chapters('text_folder/text.txt')

# BGMファイルと背景画像ファイルのパス
bgm_folder = 'bgm_folder'
background_folder = 'background_folder'

# BGMフォルダ内の最初のmp3ファイルを取得
bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith('.mp3')]
if bgm_files:
    # BGMフォルダ内の最初のmp3ファイルを取得
    bgm_file = os.path.join(bgm_folder, bgm_files[0])

    # 2章ごとにビデオを生成
    for i in range(0, len(chapters), 2):
        chapter_text = ''.join(chapters[i:i+2])  # 2章ずつのテキストを取得し、連結して単一の文字列にする
        output_file = f'output_folder/{i//2 + 1}.mp4'  # 出力ファイル名

        # BGMファイルと背景画像ファイルのパス
        background_file = os.path.join(background_folder, f'{(i//2)+1}.png')

        # create_video_from_text関数を呼び出してビデオを生成
        create_video_from_text(chapter_text, bgm_file, background_file, output_file)

    print("All videos created successfully.")
