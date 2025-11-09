"""Сервис для шифрования токенов и чувствительных данных"""
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.core.config import settings


class EncryptionService:
	"""Сервис для шифрования/дешифрования данных"""

	@staticmethod
	def _get_key() -> bytes:
		"""Получить ключ шифрования из SECRET_KEY"""
		# Используем SECRET_KEY для генерации ключа шифрования
		secret = settings.SECRET_KEY.encode()
		salt = b'creo_manager_salt'  # Фиксированная соль для консистентности
		
		kdf = PBKDF2HMAC(
			algorithm=hashes.SHA256(),
			length=32,
			salt=salt,
			iterations=100000,
			backend=default_backend()
		)
		key = base64.urlsafe_b64encode(kdf.derive(secret))
		return key

	@staticmethod
	def encrypt(data: dict) -> str:
		"""Зашифровать словарь в строку"""
		key = EncryptionService._get_key()
		fernet = Fernet(key)
		
		# Преобразуем словарь в JSON строку
		json_data = json.dumps(data)
		encrypted_data = fernet.encrypt(json_data.encode())
		
		# Возвращаем base64 строку для хранения в БД
		return base64.b64encode(encrypted_data).decode('utf-8')

	@staticmethod
	def decrypt(encrypted_string: str) -> dict:
		"""Расшифровать строку в словарь"""
		key = EncryptionService._get_key()
		fernet = Fernet(key)
		
		# Декодируем из base64
		encrypted_data = base64.b64decode(encrypted_string.encode('utf-8'))
		
		# Расшифровываем
		decrypted_data = fernet.decrypt(encrypted_data)
		
		# Преобразуем обратно в словарь
		return json.loads(decrypted_data.decode('utf-8'))



