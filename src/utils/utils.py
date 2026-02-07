import os
import warnings
import logging

from pydub import AudioSegment
from pydub.silence import split_on_silence

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)
warnings.filterwarnings(action="ignore")  # <--- ignore after imports


def mp42m4a(audio_file):
    command = f"ffmpeg -i {audio_file}.mp4 -vn -acodec copy {audio_file}.m4a >/dev/null 2>&1"
    os.system(f"rm {audio_file}.m4a >/dev/null 2>&1")
    os.system(command)


def cut_blanks(audio_file, min_silence_len, silence_thresh):
    audio_file_dir = "/".join(audio_file.split("/")[:-1])
    audio_file_name = audio_file.split("/")[-1]
    os.system(f"rm -rf {audio_file_dir}/chunks/ >/dev/null 2>&1")
    os.system(f"mkdir -p {audio_file_dir}/chunks/ >/dev/null 2>&1")
    sound_file = AudioSegment.from_file(f"{audio_file}.m4a", format="m4a")
    audio_chunks = split_on_silence(
        sound_file,
        # must be silent for at least 150 ms
        min_silence_len=min_silence_len,
        # consider it silent if quieter than -40 dBFS
        silence_thresh=silence_thresh,
    )
    for i, chunk in enumerate(audio_chunks):
        out_file = f"{audio_file_dir}/chunks/{audio_file_name}_chunk{i}.wav"
        # print("exporting", out_file)
        chunk.export(out_file, format="wav")
    return len(audio_chunks)


def audio_paths(audio_file):
    audio_file_dir = "/".join(audio_file.split("/")[:-1])
    audio_file_name = audio_file.split("/")[-1]
    return audio_file_dir, audio_file_name


def format_duration(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"
