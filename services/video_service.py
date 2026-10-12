"""MoviePy based server-side trimming and video export."""
import os
import uuid
import math
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, vfx


def create_motion_video(output_path, prompt, duration=10, aspect_ratio='16:9', accent='#67e8f9', image_path=None):
    """Create an original animated title card using MoviePy and Pillow."""
    duration = max(3, min(float(duration), 120))
    sizes = {'16:9': (1280, 720), '9:16': (720, 1280), '1:1': (960, 960)}
    width, height = sizes.get(aspect_ratio, sizes['16:9'])
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', accent):
        accent = '#67e8f9'

    if image_path:
        source = Image.open(image_path).convert('RGB')
        scale = max(width / source.width, height / source.height)
        source = source.resize((round(source.width * scale), round(source.height * scale)), Image.Resampling.LANCZOS)
        left, top_crop = (source.width - width) // 2, (source.height - height) // 2
        background = source.crop((left, top_crop, left + width, top_crop + height))
        shade = Image.new('RGB', (width, height), (5, 9, 20))
        background = Image.blend(background, shade, 0.48)
        draw = ImageDraw.Draw(background)
    else:
        background = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(background)
        top = (12, 18, 37)
        bottom = (42, 24, 92)
        for y in range(height):
            blend = y / max(1, height - 1)
            color = tuple(round(top[i] * (1 - blend) + bottom[i] * blend) for i in range(3))
            draw.line((0, y, width, y), fill=color)

    font_path = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts', 'arial.ttf')
    try:
        title_font = ImageFont.truetype(font_path, max(36, round(min(width, height) * 0.075)))
        subtitle_font = ImageFont.truetype(font_path, max(20, round(min(width, height) * 0.027)))
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    title = ' '.join(prompt.split())[:120]
    words = title.split()
    lines, line = [], ''
    max_width = width * 0.82
    for word in words:
        candidate = f'{line} {word}'.strip()
        if draw.textlength(candidate, font=title_font) > max_width and line:
            lines.append(line)
            line = word
            if len(lines) == 3:
                break
        else:
            line = candidate
    if line and len(lines) < 3:
        lines.append(line)
    title_block_height = len(lines) * (title_font.size * 1.2)
    center_y = height * 0.49
    first_y = center_y - title_block_height / 2
    for index, text in enumerate(lines):
        draw.text((width / 2, first_y + index * title_font.size * 1.2), text,
                  font=title_font, fill='white', anchor='mm', stroke_width=1, stroke_fill=(10, 13, 29))
    draw.rounded_rectangle((width * 0.42, center_y + title_block_height / 2 + height * 0.035,
                            width * 0.58, center_y + title_block_height / 2 + height * 0.047),
                           radius=8, fill=accent)
    draw.text((width / 2, center_y + title_block_height / 2 + height * 0.105),
              'CREATED WITH MOVIEPY  ·  CREATORA STUDIO', font=subtitle_font,
              fill=(205, 214, 236), anchor='mm')
    base_frame = np.asarray(background)
    accent_rgb = tuple(int(accent[i:i + 2], 16) for i in (1, 3, 5))
    radius = max(10, round(min(width, height) * 0.018))

    def frame_at(time):
        frame = Image.fromarray(base_frame.copy())
        frame_draw = ImageDraw.Draw(frame)
        orbit_radius = min(width, height) * 0.31
        x = width / 2 + math.cos(time * 0.75) * orbit_radius
        y = height / 2 + math.sin(time * 0.75) * orbit_radius * 0.52
        frame_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=accent_rgb)
        return np.asarray(frame)

    animated = VideoClip(frame_function=frame_at, duration=duration).with_fps(24)
    try:
        animated.write_videofile(output_path, codec='libx264', audio=False, fps=24, logger=None)
    finally:
        animated.close()


def render_video(source_path, output_path, start=0, end=None, title='', brightness=1.0):
    """Trim, fit to 720p landscape, optionally title and adjust brightness."""
    clip = VideoFileClip(source_path)
    layers = []
    try:
        start = max(0.0, min(float(start), max(clip.duration - 0.1, 0)))
        end = clip.duration if end is None else min(float(end), clip.duration)
        if end <= start:
            raise ValueError('End time must be after start time.')
        clip = clip.subclipped(start, end)
        clip = clip.resized(height=720)
        if clip.w < 1280:
            clip = clip.resized(width=1280)
        clip = clip.with_effects([vfx.Crop(width=1280, height=720, x_center=clip.w / 2, y_center=clip.h / 2)])
        clip = clip.with_effects([vfx.MultiplyColor(max(0.2, min(float(brightness), 2.0)))])
        if title.strip():
            image = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            font_path = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts', 'arial.ttf')
            try:
                font = ImageFont.truetype(font_path, 58)
            except OSError:
                font = ImageFont.load_default()
            text = title.strip()[:120]
            box = draw.textbbox((0, 0), text, font=font)
            text_width = box[2] - box[0]
            x = max(48, (1280 - text_width) / 2)
            draw.text((x, 540), text, font=font, fill='white', stroke_width=2, stroke_fill=(0, 0, 0, 180))
            layers.append(ImageClip(np.asarray(image)).with_duration(clip.duration).with_position(('center', 'center')))
        final = CompositeVideoClip([clip, *layers], size=(1280, 720)) if layers else clip
        final.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=clip.fps or 24, logger=None)
        if final is not clip:
            final.close()
    finally:
        clip.close()
        for layer in layers:
            layer.close()
