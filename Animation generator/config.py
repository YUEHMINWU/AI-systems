import os

class Config:
    TEMP_DIR = "assets/temp"
    OUTPUT_DIR = "assets/JP_hor_wc"
    RESOLUTION = (1280, 720)
    AUDIO_FPS = 44100
    TRANSITION_DURATION = 0.5
    SUBTITLE_STYLE = {
        "fontname": "Arial",
        "fontsize": 16,
        "color": "&H00FFFFFF",
        "bg_color": "&H80000000",
        "outline": 1
    }
    TTS_VOICE = "en-US-AriaNeural"
    SDXL_ENDPOINT = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0" # Choose the text-to-image model in Hugging Face Hub
    HF_TOKEN = os.environ['HF_TOKEN'] # export HF_TOKEN = "Your_API_Key"
    FALAI_KEY = os.environ['FALAI_KEY'] # export FALAI_KEY = "Your_API_Key"

    @staticmethod
    def get_scene_duration(num_scenes):
        target_duration = 600  # Target 600 seconds
        transition_duration = Config.TRANSITION_DURATION  # 0.5 seconds
        return (target_duration - (num_scenes - 1) * transition_duration) / num_scenes
