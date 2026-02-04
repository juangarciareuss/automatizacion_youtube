from moviepy.editor import vfx

class VisualEffects:
    def __init__(self, width=1080, height=1920):
        self.width = width
        self.height = height

    def apply_ken_burns(self, clip, zoom_factor=0.04):
        """Aplica Zoom In progresivo."""
        return clip.resize(lambda t: 1 + zoom_factor * t)

    def resize_to_fill(self, clip):
        """Ajuste Center Crop inteligente para llenar 1080x1920."""
        target_ratio = self.width / self.height
        img_w, img_h = clip.size
        img_ratio = img_w / img_h

        if img_ratio > target_ratio:
            new_height = self.height
            new_width = int(new_height * img_ratio)
        else:
            new_width = self.width
            new_height = int(new_width / img_ratio)

        clip = clip.resize(newsize=(new_width, new_height))
        
        x_center = new_width / 2
        y_center = new_height / 2
        
        clip = clip.crop(
            x1=x_center - (self.width / 2),
            y1=y_center - (self.height / 2),
            width=self.width,
            height=self.height
        )
        return clip

    def apply_crossfade(self, clip, duration=0.8):
        """Disolvencia suave de entrada."""
        return clip.crossfadein(duration)