import json
from typing import Dict
from config import Config
# You can use LLM chatbox to generate high quality and accurate scripts in json format
class StoryGenerator:
    def validate_script(self, script_json: str) -> Dict:
        try:
            json_data = json.loads(script_json)
            if not isinstance(json_data, dict) or "scenes" not in json_data:
                raise ValueError("Invalid JSON structure - missing 'scenes' key")
            if not isinstance(json_data["scenes"], list):
                raise ValueError("'scenes' must be an array")
            num_scenes = len(json_data["scenes"])
            if num_scenes < 50 or num_scenes > 65:
                print(f"⚠️ Warning: Provided {num_scenes} scenes, expected 50–65.")
            for scene in json_data["scenes"]:
                if not scene.get("narration") or len(scene["narration"].strip().split()) < 10:
                    scene["narration"] = "A restless spirit haunts the cursed shrine in eternal darkness."
                if not scene.get("visual"):
                    scene["visual"] = "A misty shrine under moonlight with a ghostly figure."
                if not scene.get("mood"):
                    scene["mood"] = "eerie"
            return json_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
