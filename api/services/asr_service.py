"""ASR and alignment service."""
import os
import json
import datetime
import subprocess
from typing import Callable, Optional, List, Dict
from faster_whisper import WhisperModel
from api.services.audio_service import AudioService


def replace_special_chars(text: str) -> str:
    """Remove or replace special characters in transcription."""
    if text.startswith("! ") or text.startswith(" "):
        text = text.replace("!", "").replace(" ", "", 1)
    text = text.replace(",", "，").replace("?", "？")
    return text


def format_to_srt(seconds: float) -> str:
    """Convert seconds to SRT timecode format."""
    dt = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=seconds)
    formatted_time = "{:02d}:{:02d}:{:02d},{:03d}".format(
        dt.hour, dt.minute, dt.second, dt.microsecond // 1000
    )
    return formatted_time


class ASRService:
    """Service for ASR transcription and forced alignment."""
    
    def __init__(self, model_name: str = "deepdml/faster-whisper-large-v3-turbo-ct2"):
        """Initialize ASR service with specified model."""
        self.model_name = model_name
        self.model = None
    
    def load_model(self, device: str = "cuda", compute_type: str = "float16"):
        """Load the Whisper model."""
        if self.model is None:
            self.model = WhisperModel(self.model_name, device=device, compute_type=compute_type)
        return self.model
    
    def transcribe_audio(
        self,
        audio_file: str,
        subtitle_format: str = "txt",
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Transcribe audio file using Whisper ASR."""
        if progress_callback:
            progress_callback(f"Transcribing {os.path.basename(audio_file)}...")
        
        if self.model is None:
            self.load_model()
        
        segments, info = self.model.transcribe(
            f"{audio_file}.wav",
            word_timestamps=True,
            initial_prompt="以下是普通话的句子。",
            beam_size=5,
            language="zh",
            max_new_tokens=433,
            condition_on_previous_text=False,
            vad_filter=False,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        sub_list: List[Dict[str, str]] = []
        for segment in segments:
            start_time_str = format_to_srt(segment.start)
            end_time_str = format_to_srt(segment.end)
            sub_text = replace_special_chars(segment.text)
            
            if progress_callback:
                progress_callback(f"[{segment.start:.2f}s → {segment.end:.2f}s] {sub_text}")
            
            sub_entry = {
                "start_time_str": start_time_str,
                "end_time_str": end_time_str,
                "text": sub_text,
            }
            sub_list.append(sub_entry)
        
        self._generate_subtitles(audio_file, sub_list, subtitle_format)
        
        if progress_callback:
            progress_callback(f"Saved: {os.path.abspath(f'{audio_file}.{subtitle_format}')}")
        
        return sub_list
    
    @staticmethod
    def _generate_subtitles(audio_file: str, sub_list: List[Dict], subtitle_format: str = "srt"):
        """Generate subtitle files in specified format."""
        if subtitle_format == "srt":
            srt_content = ""
            srt_number = 1
            for sub in sub_list:
                sub_srt = f"{sub['start_time_str']} --> {sub['end_time_str']}\n{sub['text']}\n\n"
                srt_content += str(srt_number) + "\n" + sub_srt
                srt_number += 1
            with open(f"{audio_file}.srt", "w", encoding="utf-8") as srt_file:
                srt_file.write(srt_content)
        elif subtitle_format == "json":
            with open(f"{audio_file}.json", "w", encoding="utf-8") as json_file:
                json_file.write(str(sub_list).replace("'", '"'))
        elif subtitle_format == "txt":
            with open(f"{audio_file}.txt", "w", encoding="utf-8") as txt_file:
                for sub in sub_list:
                    txt_file.write(sub["text"])
    
    @staticmethod
    def mfa(audio_file_dir: str, progress_callback: Optional[Callable] = None):
        """Perform forced alignment using Montreal Forced Aligner."""
        if progress_callback:
            progress_callback("Starting Montreal Forced Aligner...")
        
        # Build MFA command
        cmd = [
            "mfa", "align",
            "--output_format", "json",
            "--use_threading",
            "--use_mp",
            "--overwrite",
            "--clean",
            "--final_clean",
            f"{audio_file_dir}/chunks",
            "mandarin_china_mfa",
            "mandarin_mfa",
            f"{audio_file_dir}/chunks"
        ]
        
        try:
            # Run MFA and capture output in real-time
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output line by line
            for line in process.stdout:
                line = line.strip()
                if line and progress_callback:
                    # Filter out very verbose lines but keep important ones
                    if any(keyword in line.lower() for keyword in [
                        'processing', 'aligning', 'complete', 'error', 'warning',
                        'done', 'finished', 'success', 'failed', 'analyzing',
                        'generating', 'loading', 'file', 'chunk'
                    ]):
                        progress_callback(f"MFA: {line}")
            
            # Wait for process to complete
            return_code = process.wait()
            
            if progress_callback:
                if return_code == 0:
                    progress_callback("✓ MFA alignment completed successfully")
                else:
                    progress_callback(f"⚠ MFA alignment completed with code {return_code}")
            
            return return_code
            
        except FileNotFoundError:
            error_msg = "MFA not found. Please ensure Montreal Forced Aligner is installed."
            if progress_callback:
                progress_callback(f"❌ Error: {error_msg}")
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"MFA execution error: {str(e)}"
            if progress_callback:
                progress_callback(f"❌ Error: {error_msg}")
            raise RuntimeError(error_msg)
    
    def process_audio_file(
        self,
        audio_file: str,
        min_silence_len: int,
        manual_silence_len: int,
        silence_thresh: int,
        progress_callback: Optional[Callable] = None
    ) -> tuple[str, str]:
        """
        Complete audio processing pipeline.
        
        Returns:
            Tuple of (combined_audio_file, combined_json_file)
        """
        audio_file_dir, audio_file_name = AudioService.audio_paths(audio_file)
        
        # Step 1: Cut audio into chunks
        if progress_callback:
            progress_callback("Step 1/4: Splitting audio into chunks...")
        chunks = AudioService.cut_blanks(
            audio_file, min_silence_len, silence_thresh, progress_callback
        )
        
        # Step 2: Transcribe each chunk
        if progress_callback:
            progress_callback(f"Step 2/4: Transcribing {chunks} chunks...")
        for i in range(chunks):
            chunk_audio_file = f"{audio_file_dir}/chunks/{audio_file_name}_chunk{i}"
            self.transcribe_audio(chunk_audio_file, subtitle_format="txt", progress_callback=progress_callback)
        
        # Step 3: Perform MFA alignment
        if progress_callback:
            progress_callback("Step 3/4: Performing forced alignment...")
        self.mfa(audio_file_dir, progress_callback)
        
        # Step 4: Concatenate audio and timestamps
        if progress_callback:
            progress_callback("Step 4/4: Concatenating audio and timestamps...")
        combined_audio_file, combined_json_file = AudioService.concatenate_audio_and_adjust_timestamps(
            audio_file, chunks, manual_silence_len, progress_callback
        )
        
        if progress_callback:
            progress_callback("Processing complete!")
        
        return combined_audio_file, combined_json_file
