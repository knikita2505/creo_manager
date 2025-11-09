"""Сервис для работы с Telegram Bot API"""
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings


class TelegramService:
	"""Сервис для работы с Telegram Bot API"""

	@staticmethod
	async def test_connection(auth_data: dict) -> Dict[str, Any]:
		"""Проверить соединение с Telegram и отправить тестовое сообщение"""
		bot_token = auth_data.get("bot_token")
		if not bot_token:
			return {"status": "error", "message": "Bot token не найден"}

		try:
			# Проверяем, что бот валиден
			async with httpx.AsyncClient() as client:
				response = await client.get(
					f"https://api.telegram.org/bot{bot_token}/getMe"
				)
				if response.status_code != 200:
					return {"status": "error", "message": "Неверный bot token"}

				bot_info = response.json()
				if not bot_info.get("ok"):
					return {"status": "error", "message": bot_info.get("description", "Ошибка")}

				result = bot_info.get("result", {}) if bot_info else {}
				bot_name = result.get("username") or result.get("first_name") or "Unknown"
				return {
					"status": "ok",
					"message": f"Бот подключен: @{bot_name}" if result.get("username") else f"Бот подключен: {bot_name}",
					"meta": {
						"display_name": f"@{result.get('username')}" if result.get("username") else bot_name,
						"username": result.get("username"),
						"id": result.get("id"),
						"type": result.get("type"),
					},
				}

		except Exception as e:
			return {"status": "error", "message": str(e)}

	@staticmethod
	async def send_message(
		bot_token: str, chat_id: str, message: str
	) -> Dict[str, Any]:
		"""Отправить сообщение через Telegram"""
		try:
			async with httpx.AsyncClient() as client:
				response = await client.post(
					f"https://api.telegram.org/bot{bot_token}/sendMessage",
					json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
				)

				if response.status_code == 200:
					return {"status": "ok", "message": "Сообщение отправлено"}
				else:
					error_data = response.json()
					return {
						"status": "error",
						"message": error_data.get("description", "Ошибка отправки"),
					}

		except Exception as e:
			return {"status": "error", "message": str(e)}


