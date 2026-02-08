"""Audio processing service."""
import os
import json
import datetime
import subprocess
from typing import Dict, Callable, Optional
from pydub import AudioSegment
from pydub.silence import split_on_silence


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS:mmm format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{minutes:02d}:{secs:02d}:{milliseconds:03d}"


class AudioService:
    """Service for audio file manipulation."""
    
    @staticmethod
    def mp42m4a(audio_file: str, progress_callback: Optional[Callable] = None) -> None:
        """Convert MP4 video to M4A audio format."""
        if progress_callback:
            progress_callback("Converting MP4 to M4A...")
        
        input_file = f"{audio_file}.mp4"
        output_file = f"{audio_file}.m4a"
        
        # Remove existing output file
        if os.path.exists(output_file):
            os.remove(output_file)
        
        # Run ffmpeg with progress output
        cmd = [
            "ffmpeg", "-i", input_file,
            "-vn", "-acodec", "copy",
            "-y",  # Overwrite without asking
            output_file
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line and progress_callback:
                    # Filter for relevant ffmpeg output
                    if any(keyword in line.lower() for keyword in [
                        'duration', 'time=', 'size=', 'speed=', 'error', 'warning'
                    ]):
                        # Clean up the line
                        if 'time=' in line.lower():
                            progress_callback(f"Converting: {line.split('time=')[1].split()[0]}")
                        elif 'duration' in line.lower():
                            progress_callback(f"Input: {line}")
            
            return_code = process.wait()
            
            if return_code == 0 and progress_callback:
                progress_callback("✓ Conversion completed")
            elif progress_callback:
                progress_callback(f"⚠ Conversion completed with code {return_code}")
                
        except FileNotFoundError:
            error_msg = "ffmpeg not found. Please ensure ffmpeg is installed."
            if progress_callback:
                progress_callback(f"❌ Error: {error_msg}")
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Conversion error: {str(e)}"
            if progress_callback:
                progress_callback(f"❌ Error: {error_msg}")
            raise RuntimeError(error_msg)

    @staticmethod
    def m4a_to_wav(audio_file: str, output_file: str) -> None:
        """Convert M4A to WAV format."""
        audio = AudioSegment.from_file(audio_file, format="m4a")
        audio.export(output_file, format="wav")

    @staticmethod
    def cut_blanks(
        audio_file: str,
        min_silence_len: int,
        silence_thresh: int,
        progress_callback: Optional[Callable] = None
    ) -> int:
        """Split audio into chunks based on silence detection."""
        if progress_callback:
            progress_callback("Starting audio chunking...")
        
        audio_file_dir, audio_file_name = AudioService.audio_paths(audio_file)
        os.system(f"rm -rf {audio_file_dir}/chunks/ >/dev/null 2>&1")
        os.system(f"mkdir -p {audio_file_dir}/chunks/ >/dev/null 2>&1")
        
        if progress_callback:
            progress_callback("Loading audio file...")
        
        sound_file = AudioSegment.from_file(f"{audio_file}.m4a", format="m4a")
        
        if progress_callback:
            progress_callback("Detecting silence and splitting...")
        
        audio_chunks = split_on_silence(
            sound_file,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
        )
        
        for i, chunk in enumerate(audio_chunks):
            out_file = f"{audio_file_dir}/chunks/{audio_file_name}_chunk{i}.wav"
            chunk.export(out_file, format="wav")
        if progress_callback:
            progress_callback(f"Created {len(audio_chunks)} chunks")
        
        return len(audio_chunks)

    @staticmethod
    def audio_paths(audio_file: str) -> tuple[str, str]:
        """Extract directory and filename from audio file path."""
        audio_file_dir = "/".join(audio_file.split("/")[:-1])
        audio_file_name = audio_file.split("/")[-1]
        return audio_file_dir, audio_file_name

    @staticmethod
    def concatenate_audio_and_adjust_timestamps(
        audio_file: str,
        chunks: int,
        manual_silence_len: int,
        progress_callback: Optional[Callable] = None
    ) -> tuple[str, str]:
        """Concatenate audio files with silence intervals and adjust timestamps."""
        if progress_callback:
            progress_callback("Starting audio concatenation...")
        
        audio_file_dir, audio_file_name = AudioService.audio_paths(audio_file)
        combined_audio = AudioSegment.empty()
        combined_data = {}
        sequence = 0
        cumulative_time = 0.0

        for i in range(chunks):
            chunk_audio_file = f"{audio_file_dir}/chunks/{audio_file_name}_chunk{i}"
            wav_file_path = f"{chunk_audio_file}.wav"
            json_file_path = f"{chunk_audio_file}.json"
            
            if not os.path.exists(wav_file_path):
                if progress_callback:
                    progress_callback(f"Warning: {wav_file_path} not found, skipping...")
                continue
            
            # Load audio chunk
            audio_chunk = AudioSegment.from_file(wav_file_path, format="wav")
            combined_audio += audio_chunk
            
            # Process JSON if exists
            if os.path.exists(json_file_path):
                try:
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                    
                    if 'tiers' in chunk_data and 'words' in chunk_data['tiers']:
                        words_tier = chunk_data['tiers']['words']
                        if 'entries' in words_tier:
                            for entry in words_tier['entries']:
                                word_text = entry[2].strip()
                                if word_text and word_text != '':
                                    combined_data[sequence] = {
                                        "word": word_text,
                                        "start_time": entry[0] + cumulative_time,
                                        "end_time": entry[1] + cumulative_time
                                    }
                                    sequence += 1
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Error processing {json_file_path}: {e}")
            
            # Update cumulative time
            chunk_duration_sec = len(audio_chunk) / 1000.0
            cumulative_time += chunk_duration_sec
            
            # Add silence interval between chunks
            if i < chunks - 1:
                silence = AudioSegment.silent(duration=manual_silence_len)
                combined_audio += silence
                cumulative_time += manual_silence_len / 1000.0

        # Save combined audio file
        combined_audio_file = f"{audio_file_dir}/{audio_file_name}_combined.m4a"
        combined_audio.export(combined_audio_file, format="ipod")
        
        combined_json_file = f"{audio_file_dir}/{audio_file_name}_combined.json"
        with open(combined_json_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)

        if progress_callback:
            original_audio = AudioSegment.from_file(f"{audio_file_dir}/{audio_file_name}.m4a", format="m4a")
            original_duration = len(original_audio) / 1000.0
            combined_duration = len(combined_audio) / 1000.0
            progress_callback(f"Combined {sequence} word entries from {chunks} chunks")
            progress_callback(f"Original: {format_duration(original_duration)}, Combined: {format_duration(combined_duration)}")
        
        return combined_audio_file, combined_json_file

    @staticmethod
    def align_audio_with_edited_json(
        original_json_file: str,
        edited_json_file: str,
        original_audio_file: str,
        output_audio_file: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Generate aligned audio based on edited JSON."""
        if progress_callback:
            progress_callback("Loading JSON files...")
        
        # Load both JSON files
        with open(original_json_file, 'r', encoding='utf-8') as f:
            original_data = {int(k): v for k, v in json.load(f).items()}
        
        with open(edited_json_file, 'r', encoding='utf-8') as f:
            edited_data = {int(k): v for k, v in json.load(f).items()}
        
        if progress_callback:
            progress_callback("Loading original audio...")
        
        # Load original audio
        original_audio = AudioSegment.from_file(original_audio_file, format="m4a")
        original_duration = len(original_audio) / 1000.0
        end_ms = len(original_audio)
        rm_sequence = 0
        
        if progress_callback:
            progress_callback("Processing audio alignment...")
        
        # Iterate through edited data in order
        for seq_id in reversed(sorted(original_data.keys())):
            if seq_id not in edited_data:
                original_entry = original_data.get(str(seq_id), original_data.get(seq_id))
                
                if seq_id + 1 in edited_data:
                    end_ms = int(original_entry['end_time'] * 1000)
                if seq_id - 1 not in edited_data:
                    rm_sequence += 1
                    continue
                
                start_ms = int(original_entry['start_time'] * 1000)
                original_audio = original_audio[:start_ms] + original_audio[end_ms:]
                rm_sequence += 1
        
        if progress_callback:
            progress_callback("Exporting aligned audio...")
        
        # Export new audio file
        original_audio.export(output_audio_file, format="ipod")
        
        new_duration = len(original_audio) / 1000.0
        
        result = {
            "original_segments": len(original_data),
            "removed_segments": rm_sequence,
            "remaining_segments": len(original_data) - rm_sequence,
            "original_duration": format_duration(original_duration),
            "new_duration": format_duration(new_duration),
            "output_file": output_audio_file
        }
        
        if progress_callback:
            progress_callback(f"Removed {rm_sequence} segments, {result['remaining_segments']} remaining")
            progress_callback(f"Duration: {result['original_duration']} → {result['new_duration']}")
        
        return result
