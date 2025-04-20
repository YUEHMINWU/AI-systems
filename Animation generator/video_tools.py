from moviepy.editor import *
from config import Config
import os
import gc
import tempfile

class VideoAssembler:
    def compile_video(self, story, num_scenes, scene_duration, theme="final"):
        clips = []
        temp_dir = tempfile.gettempdir()
        print(f"Using temporary directory for MoviePy: {temp_dir}")

        for i in range(num_scenes):
            scene_path = f"{Config.TEMP_DIR}/scene_{i}.mp4"
            try:
                if not os.path.exists(scene_path):
                    print(f"⚠️ Scene file {scene_path} missing, skipping")
                    continue
                clip = VideoFileClip(scene_path)
                if clip.duration < scene_duration - 0.01 or clip.duration > scene_duration + 0.01:
                    print(f"⚠️ Scene {i} duration {clip.duration}s deviates from expected {scene_duration}s, adjusting")
                    if clip.duration > scene_duration:
                        clip = clip.subclip(0, scene_duration)
                    else:
                        clip = clip.fx(vfx.loop, duration=scene_duration)
                if clip.audio:
                    clip = clip.set_audio(clip.audio.set_fps(Config.AUDIO_FPS))
                if i > 0:
                    clip = clip.crossfadein(Config.TRANSITION_DURATION)
                clips.append(clip)
                print(f"✅ Loaded scene {i}: duration={clip.duration}s")
                gc.collect()
            except Exception as e:
                print(f"⚠️ Failed to load {scene_path}: {str(e)}")
                continue

        if not clips:
            raise ValueError(f"No valid clips were loaded for assembly. Checked {num_scenes} scenes.")

        print("📽️ Concatenating clips...")
        final = concatenate_videoclips(clips, method="compose", padding=-Config.TRANSITION_DURATION)

        print("🎨 Applying effects...")
        if final.audio:
            final = final.set_audio(final.audio.set_fps(Config.AUDIO_FPS))
            try:
                final = final.set_audio(final.audio.fx(afx.audio_normalize))
            except Exception as e:
                print(f"⚠️ Audio normalization failed: {str(e)}. Proceeding without normalization.")

        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        output_path = f"{Config.OUTPUT_DIR}/{theme}.mp4"
        print(f"💾 Writing final video to {output_path}...")
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            threads=1,
            fps=20,
            temp_audiofile=os.path.join(temp_dir, "temp-audio.m4a")
        )

        final.close()
        for clip in clips:
            clip.close()
        gc.collect()
        
        print(f"✅ Final video written to {output_path}")
