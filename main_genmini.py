from qa_extractor.extractor import extract_qa_from_audio_genmini
from qa_extractor.extractor import save_to_json
import prompts

def main(audio_file):
    result = extract_qa_from_audio_genmini(audio_file)
    print(result)

    save_to_json(result,"test.json")

if __name__ == "__main__":
    main("videoplayback_audio.mp3") 