import json
import os
from typing import Any, Dict, List, Optional, Tuple

# Путь к файлу с пользователями
DEFAULT_PATH = "users.json"

# Загрузка всех пользователей
def load_users(path: str = DEFAULT_PATH) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    return data

# Сохранение всех пользователей
def save_users(data: Dict[str, Any], path: str = DEFAULT_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Получение данных конкретного пользователя
def get_user(user_id: str, path: str = DEFAULT_PATH) -> Optional[Dict[str, Any]]:
    data = load_users(path)
    return data.get(user_id)

# Проверка, есть ли пользователь
def has_user(user_id: str, path: str = DEFAULT_PATH) -> bool:
    data = load_users(path)
    return user_id in data

# Создание или обновление пользователя
def upsert_user(user_id: str, payload: Dict[str, Any], path: str = DEFAULT_PATH) -> None:
    data = load_users(path)
    data[user_id] = payload
    save_users(data, path)

# Удаление пользователя
def delete_user(user_id: str, path: str = DEFAULT_PATH) -> bool:
    data = load_users(path)
    if user_id in data:
        del data[user_id]
        save_users(data, path)
        return True
    return False

# Поиск пользователей по значению поля
def find_by_field(field: str, value: Any, path: str = DEFAULT_PATH) -> List[Tuple[str, Dict[str, Any]]]:
    data = load_users(path)
    res: List[Tuple[str, Dict[str, Any]]] = []
    for uid, u in data.items():
        if isinstance(u, dict) and u.get(field) == value:
            res.append((uid, u))
    return res

# Загрузка интересных фактов
with open("int_facts.json", "r", encoding="utf-8") as f:
    space_facts = json.load(f)