import json
import logging
from video_automated import VideoSuiteAutomated

print("Starting custom direct longform assembly run...")
app = VideoSuiteAutomated()
with open('posts_data_longform.json', 'r') as f:
    app.projects = json.load(f)

app.assemble_longform_video()
print("Done!")
