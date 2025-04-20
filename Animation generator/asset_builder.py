import os
import requests
import edge_tts
import asyncio
from moviepy.editor import AudioClip, AudioFileClip
from config import Config
import fal_client
from math import ceil

os.environ['FAL_KEY'] = Config.FALAI_KEY

class AssetBuilder:
    def process_scene(self, scene, idx, force_regenerate=False, num_scenes=57, scene_duration=10.0):
        print(f"🎬 Generating assets for Scene {idx+1}")
        img_path = f"{Config.TEMP_DIR}/scene_{idx}.png"
        bgm_path = f"{Config.TEMP_DIR}/bgm_{idx}.wav"
        if force_regenerate or not os.path.exists(img_path):
            img_path = self._generate_image(scene['visual'], idx)
        if force_regenerate or not os.path.exists(bgm_path):
            bgm_path = self._generate_bgm(scene['mood'], idx, num_scenes, scene_duration)
        voice_path = self._generate_voice(scene['narration'], idx, scene_duration)
        sub_path = self._create_subtitle(scene['narration'], voice_path, idx, num_scenes, scene_duration)
        self._render_scene(img_path, bgm_path, voice_path, sub_path, idx, num_scenes, scene_duration)

    def _generate_image(self, prompt, idx):
        try:
            response = requests.post(
                Config.SDXL_ENDPOINT,
                headers={"Authorization": f"Bearer {Config.HF_TOKEN}"},
                json={
                    "inputs": f"Japanese watercolor horror style, {prompt}",
                    "parameters": {"guidance_scale": 12.5}
                }
            )
            img_path = f"{Config.TEMP_DIR}/scene_{idx}.png"
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            with open(img_path, "wb") as f:
                f.write(response.content)
            return img_path
        except Exception as e:
            print(f"⚠️ Image generation failed: {str(e)}, using fallback")
            return self._create_fallback_image(idx)

    def _generate_bgm(self, mood, idx, num_scenes, scene_duration):
        try:
            prompt = f"{mood} horror ambient using appropriate Japanese stringed instruments"
            duration = ceil(scene_duration)
            handler = fal_client.submit(
                "cassetteai/sound-effects-generator",
                arguments={
                    "prompt": prompt,
                    "duration": min(duration, 30)
                }
            )
            result = fal_client.result("cassetteai/sound-effects-generator", handler.request_id)
            audio_url = result["audio_file"]["url"]
            bgm_path = f"{Config.TEMP_DIR}/bgm_{idx}.wav"
            os.makedirs(os.path.dirname(bgm_path), exist_ok=True)
            response = requests.get(audio_url)
            with open(bgm_path, "wb") as f:
                f.write(response.content)
            return bgm_path
        except Exception as e:
            print(f"⚠️ BGM generation failed: {str(e)}, using silent audio")
            return self._create_silent_audio(idx, scene_duration)

    def _generate_voice(self, text, idx, scene_duration):
        voice_path = f"{Config.TEMP_DIR}/voice_{idx}.wav"
        rate = "-30%"  # Default
        if scene_duration < 9:
            rate = "-20%"  # Faster for shorter scenes
        elif scene_duration > 11:
            rate = "-40%"  # Slower for longer scenes
        communicate = edge_tts.Communicate(text[:500], Config.TTS_VOICE, rate=rate)
        try:
            asyncio.run(communicate.save(voice_path))
            if os.path.exists(voice_path) and os.path.getsize(voice_path) > 0:
                return voice_path
            else:
                raise Exception("Edge-tts generated an empty file")
        except Exception as e:
            print(f"❌ Edge-tts failed for Scene {idx+1}: {str(e)}, using silent audio")
            return self._create_silent_audio(idx, scene_duration)

    def _create_subtitle(self, text, audio_path, idx, num_scenes, scene_duration):
        sub_path = f"{Config.TEMP_DIR}/sub_{idx}.srt"
        try:
            with AudioFileClip(audio_path) as clip:
                duration = clip.duration
        except Exception as e:
            print(f"⚠️ Failed to read audio duration: {str(e)}, using 90% of scene duration")
            duration = scene_duration * 0.9

        sentences = [s.strip() for s in text.split('.')] if '.' in text else [text]
        sentences = [s for s in sentences if s]
        num_subtitles = max(1, len(sentences))
        subtitle_duration = (duration / num_subtitles) if duration > 0 else (scene_duration * 0.9)

        with open(sub_path, "w") as f:
            for i, sentence in enumerate(sentences, start=1):
                start_time = self._seconds_to_srt_time((i - 1) * subtitle_duration)
                end_time = self._seconds_to_srt_time(min(i * subtitle_duration, scene_duration * 0.9))
                if len(sentence) > 40:
                    words = sentence.split()
                    lines = []
                    current_line = []
                    current_len = 0
                    for word in words:
                        if current_len + len(word) + 1 <= 40:
                            current_line.append(word)
                            current_len += len(word) + 1
                        else:
                            lines.append(" ".join(current_line))
                            current_line = [word]
                            current_len = len(word) + 1
                    if current_line:
                        lines.append(" ".join(current_line))
                    sentence = "\n".join(lines)
                f.write(f"{i}\n{start_time} --> {end_time}\n{sentence}\n\n")
        return sub_path

    def _create_silent_audio(self, idx, duration):
        silent_clip = AudioClip(lambda t: 0, duration=duration)
        audio_path = f"{Config.TEMP_DIR}/silent_{idx}.wav"
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        silent_clip.write_audiofile(audio_path, fps=44100, nbytes=2, codec='pcm_s16le')
        return audio_path

    def _seconds_to_srt_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def _render_scene(self, img_path, bgm_path, voice_path, sub_path, idx, num_scenes, scene_duration):
        for path in [img_path, bgm_path, voice_path, sub_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Required file {path} not found")
        ffmpeg_cmd = f"""
        ffmpeg -y -loop 1 -i "{img_path}" -i "{bgm_path}" -i "{voice_path}" \
        -filter_complex "
        [0]scale={Config.RESOLUTION[0]}:{Config.RESOLUTION[1]},zoompan=z='min(zoom+0.001,1.3)':d=1:s={Config.RESOLUTION[0]}x{Config.RESOLUTION[1]}[vid];
        [vid]subtitles='{sub_path}':force_style='FontName={Config.SUBTITLE_STYLE['fontname']},FontSize={Config.SUBTITLE_STYLE['fontsize']},PrimaryColour={Config.SUBTITLE_STYLE['color']},BackColour={Config.SUBTITLE_STYLE['bg_color']},Outline={Config.SUBTITLE_STYLE['outline']}'[out];
        [1:a]volume=0.3[a1];[2:a]volume=1.0[a2];[a1][a2]amix=inputs=2:duration=longest[a]
        " -map "[out]" -map "[a]" \
        -t {scene_duration} \
        -c:v libx264 -preset fast -c:a aac \
        "{Config.TEMP_DIR}/scene_{idx}.mp4"
        """
        result = os.system(ffmpeg_cmd)
        if result != 0:
            raise RuntimeError(f"FFmpeg failed for scene {idx}")
        print(f"✅ Rendered scene {idx}")

    def _create_fallback_image(self, idx):
        img_path = f"{Config.TEMP_DIR}/fallback_{idx}.png"
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        with open(img_path, "wb") as f:
            f.write(requests.get("https://via.placeholder.com/1920x1080").content)
        return img_path
