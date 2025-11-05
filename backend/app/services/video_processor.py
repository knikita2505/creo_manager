import os
import random
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional
import ffmpeg
from mutagen import File as MutagenFile

from app.core.config import settings


class VideoProcessor:
	"""Обработка видео: очистка метаданных, уникализация, генерация ориентаций"""

	@staticmethod
	async def get_video_info(file_path: str) -> Dict[str, float]:
		"""Получить информацию о видео"""
		probe = ffmpeg.probe(file_path)
		video_stream = next(
			(stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
		)
		if not video_stream:
			raise ValueError("Видео поток не найден")

		return {
			"duration": float(probe["format"]["duration"]),
			"width": int(video_stream["width"]),
			"height": int(video_stream["height"]),
			"fps": eval(video_stream["r_frame_rate"]),
		}

	@staticmethod
	async def clean_metadata(input_path: str, output_path: str) -> str:
		"""Очистка метаданных из видео"""
		# Используем subprocess для более точного контроля параметров ffmpeg
		cmd = [
			"ffmpeg",
			"-i", input_path,
			"-map_metadata", "-1",
			"-map_metadata:s:v", "-1",
			"-map_metadata:s:a", "-1",
			"-c", "copy",
			"-y",  # overwrite output
			output_path
		]
		
		subprocess.run(cmd, check=True, capture_output=True)

		# Дополнительная очистка через mutagen для аудио
		if os.path.exists(output_path):
			try:
				audio_file = MutagenFile(output_path)
				if audio_file:
					audio_file.delete()
					audio_file.save()
			except Exception:
				pass  # Игнорируем ошибки очистки аудио метаданных

		return output_path

	@staticmethod
	async def uniquify_video(
		input_path: str, output_path: str, info: Dict[str, float]
	) -> Tuple[str, Dict]:
		"""Уникализация видео: изменение длительности, размера, FPS, битрейта"""
		# Генерируем случайные изменения
		duration_change = random.uniform(-0.1, 0.1)
		fps_change_percent = random.uniform(-0.01, 0.01)
		bitrate_change_percent = random.uniform(-0.01, 0.01)

		new_duration = info["duration"] + duration_change
		new_fps = info["fps"] * (1 + fps_change_percent)

		# Вычисляем битрейт (приблизительно)
		file_size = os.path.getsize(input_path)
		original_bitrate = (file_size * 8) / info["duration"]
		new_bitrate = int(original_bitrate * (1 + bitrate_change_percent))

		# Применяем изменения
		stream = ffmpeg.input(input_path)
		stream = ffmpeg.filter(stream, "setpts", f"PTS-STARTPTS")
		stream = ffmpeg.output(
			stream,
			output_path,
			t=new_duration,
			r=new_fps,
			b=new_bitrate,
			codec="libx264",
			preset="medium",
			crf=23,
		)

		ffmpeg.run(stream, overwrite_output=True, quiet=True)

		transform_profile = {
			"duration_change": duration_change,
			"fps_change_percent": fps_change_percent,
			"bitrate_change_percent": bitrate_change_percent,
		}

		return output_path, transform_profile

	@staticmethod
	async def generate_orientation(
		input_path: str, output_path: str, orientation: str, original_info: Dict[str, float]
	) -> Dict[str, float]:
		"""Генерация ориентации: square (1:1), portrait (9:16), landscape (16:9)"""
		width = original_info["width"]
		height = original_info["height"]

		if orientation == "square":
			target_size = min(width, height)
			vf = f"scale={target_size}:{target_size}:force_original_aspect_ratio=decrease,pad={target_size}:{target_size}:(ow-iw)/2:(oh-ih)/2"
			new_width = target_size
			new_height = target_size
		elif orientation == "portrait":
			# 9:16
			target_height = height
			target_width = int(target_height * 9 / 16)
			if target_width > width:
				target_width = width
				target_height = int(target_width * 16 / 9)
			vf = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
			new_width = target_width
			new_height = target_height
		elif orientation == "landscape":
			# 16:9
			target_width = width
			target_height = int(target_width * 9 / 16)
			if target_height > height:
				target_height = height
				target_width = int(target_height * 16 / 9)
			vf = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
			new_width = target_width
			new_height = target_height
		else:
			raise ValueError(f"Неизвестная ориентация: {orientation}")

		stream = ffmpeg.input(input_path)
		stream = ffmpeg.filter(stream, "scale", new_width, new_height)
		stream = ffmpeg.filter(stream, "pad", new_width, new_height, "(ow-iw)/2", "(oh-ih)/2")
		stream = ffmpeg.output(stream, output_path, vcodec="libx264", preset="medium", crf=23)

		ffmpeg.run(stream, overwrite_output=True, quiet=True)

		return {
			"duration": original_info["duration"],
			"width": new_width,
			"height": new_height,
			"fps": original_info["fps"],
		}

	@staticmethod
	async def extract_thumbnail(video_path: str, output_path: str) -> str:
		"""Извлечь первый кадр как превью"""
		ffmpeg.input(video_path, ss="00:00:00").output(
			output_path, vframes=1
		).overwrite_output().run(quiet=True)
		return output_path

