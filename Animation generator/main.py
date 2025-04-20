import json
import glob
import re
from config import Config
from utils.story_gen import StoryGenerator
from utils.asset_builder import AssetBuilder
from utils.video_tools import VideoAssembler

def main():
    print("🌸 Video Generator 🌸")
    try:
        mode = input("Select mode (full/assemble-only): ").strip().lower()
        if mode not in ['full', 'assemble-only']:
            raise ValueError("Mode must be 'full' or 'assemble-only'")

        # Prompt for theme in both modes
        theme = input("Please input theme: ").strip().lower()
        # Sanitize theme for filename: replace spaces with underscores, remove special characters
        safe_theme = re.sub(r'[^a-z0-9_]', '', theme.replace(' ', '_'))
        if not safe_theme:
            raise ValueError("Theme name is invalid after sanitization (please use alphanumeric characters)")

        if mode == 'full':
            print("Paste your JSON script below (end with an empty line):")
            script_lines = []
            while True:
                line = input()
                if line == "":
                    break
                script_lines.append(line)
            script_json = "\n".join(script_lines)
            story_gen = StoryGenerator()
            story = story_gen.validate_script(script_json)
            num_scenes = len(story['scenes'])
            scene_duration = Config.get_scene_duration(num_scenes)
            total_duration = num_scenes * scene_duration + (num_scenes - 1) * Config.TRANSITION_DURATION
            print(f"✅ Validated {num_scenes} scenes. Estimated video length: {total_duration/60:.1f} minutes")
            print(f"Each scene: {scene_duration:.2f} seconds")

            print(f"\n🎥 Processing {num_scenes} scenes...")
            builder = AssetBuilder()
            for idx, scene in enumerate(story["scenes"]):
                print(f"\nScene {idx+1}: {scene['narration'][:50]}...")
                builder.process_scene(scene, idx, force_regenerate=True, num_scenes=num_scenes, scene_duration=scene_duration)
        else:
            print("\n📽️ Assembling existing scene_*.mp4 files...")
            scene_files = sorted(glob.glob(f"{Config.TEMP_DIR}/scene_*.mp4"))
            num_scenes = len(scene_files)
            if num_scenes < 1:
                raise ValueError(f"No scene_*.mp4 files found in {Config.TEMP_DIR}")
            scene_duration = Config.get_scene_duration(num_scenes)
            total_duration = num_scenes * scene_duration + (num_scenes - 1) * Config.TRANSITION_DURATION
            print(f"Found {num_scenes} scenes. Target scene duration: {scene_duration:.2f} seconds")
            print(f"Estimated video length: {total_duration/60:.1f} minutes")
            story = {"scenes": [{"visual": "", "narration": "", "mood": ""} for _ in range(num_scenes)]}  # Dummy story

        print("\n🎞️ Assembling final video...")
        # Pass the sanitized theme to compile_video
        VideoAssembler().compile_video(story, num_scenes=num_scenes, scene_duration=scene_duration, theme=safe_theme)
        
        print(f"\nKeeping temporary files in {Config.TEMP_DIR}")
        print(f"\n✅ Completed! Video saved to: {Config.OUTPUT_DIR}/{safe_theme}.mp4")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Please check inputs, asset files, or logs for details.")

if __name__ == "__main__":
    main()
