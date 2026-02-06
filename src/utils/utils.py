import datetime
import json
import os
import warnings
import logging

from pydub import AudioSegment
from pydub.silence import split_on_silence

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)
warnings.filterwarnings(action="ignore")  # <--- ignore after imports


def mp42wav(audio_file):
    command = f"ffmpeg -i {audio_file}.mp4 {audio_file}.wav >/dev/null 2>&1"
    os.system(command)


def cut_blanks(audio_file, min_silence_len, silence_thresh):
    audio_file_dir = "/".join(audio_file.split("/")[:-1])
    audio_file_name = audio_file.split("/")[-1]
    os.system(f"rm -rf {audio_file_dir}/chunks/ >/dev/null 2>&1")
    os.system(f"mkdir -p {audio_file_dir}/chunks/ >/dev/null 2>&1")
    sound_file = AudioSegment.from_wav(f"{audio_file}.wav")
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
