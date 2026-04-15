from pathlib import Path
from components.video.video_automated import VideoSuiteAutomated
from PIL import Image

class TestSuite(VideoSuiteAutomated):
    def _render_github_scroll_ffmpeg(self, screenshot_path: str, output_path: Path, duration: float = 38.0):
        from PIL import Image
        import subprocess

        FPS       = 30
        W, H      = 1920, 1080
        BG        = (8, 12, 20)
        MIN_SCALE = 0.28
        MAX_SCROLL_PX = 2200
        ZOOM_S    = 2.0

        duration = min(duration, 30.0)
        zoom_in_f  = int(ZOOM_S * FPS)
        zoom_out_f = int(ZOOM_S * FPS)
        scroll_f   = int(duration * FPS) - zoom_in_f - zoom_out_f
        total_f    = zoom_in_f + scroll_f + zoom_out_f

        src = Image.open(screenshot_path).convert('RGB')
        sw, sh = src.size
        scaled_h = int(sh * (W / sw))
        src = src.resize((W, scaled_h), Image.LANCZOS)

        cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-s', f'{W}x{H}', '-pix_fmt', 'rgb24', '-r', str(FPS),
            '-i', 'pipe:0',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p',
            str(output_path),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            for n in range(total_f):
                frame = Image.new('RGB', (W, H), BG)
                proc.stdin.write(frame.tobytes())
            
            _, stderr = proc.communicate()
            print("Communicate finished. Return code:", proc.returncode)
        except Exception as e:
            print(f"Error caught: {e}")

suite = TestSuite()
suite._render_github_scroll_ffmpeg('test_dummy.png', Path('test_out.mp4'), duration=5.0)
