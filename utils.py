def requirements_to_list(req_file="requirements.txt"):
    requirements = []
    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements

#from pydub import AudioSegment

# need install ffmpeg
#def convert_m4a_to_wav(src, export_file):
#    audio = AudioSegment.from_file(src)
#    audio = audio.set_frame_rate(16000)
#    audio = audio.set_channels(1)
#    audio = audio.set_sample_width(2)
#    audio.export(export_file, format="wav")
