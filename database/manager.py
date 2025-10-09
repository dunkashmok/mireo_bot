import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional

class JSONDatabase:
    def __init__(self, file_path='database/profiles.json'):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Создает файл и папку если их нет"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            initial_data = {
                "profiles": {},
                "likes": {},
                "superlikes": {},
                "reports": {},
                "settings": {
                    "last_cleanup": datetime.now().isoformat()
                }
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict:
        """Загружает данные из JSON файла"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return {"profiles": {}, "likes": {}, "superlikes": {}, "reports": {}, "settings": {}}
    
    def _save_data(self, data: Dict):
        """Сохраняет данные в JSON файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")
            return False
    
    def save_profile(self, user_id: int, profile_data: Dict) -> bool:
        """Сохраняет или обновляет профиль пользователя"""
        data = self._load_data()
        
        # ⚠️ ВАЖНО: добавляем user_id в данные профиля
        profile_data['user_id'] = user_id
        profile_data['last_updated'] = datetime.now().isoformat()
        profile_data['is_active'] = True
        
        data['profiles'][str(user_id)] = profile_data
        return self._save_data(data)
    
    def get_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль пользователя"""
        data = self._load_data()
        profile = data['profiles'].get(str(user_id))
        if profile:
            # Убеждаемся, что user_id есть в профиле
            profile['user_id'] = user_id
        return profile
    
    def get_random_profile(self, exclude_user_id: int = None, filters: Dict = None) -> Optional[Dict]:
        """Получает случайный профиль с фильтрами"""
        data = self._load_data()
        profiles = data['profiles']
        
        print(f"🔍 БАЗА ДАННЫХ: всего профилей = {len(profiles)}")
        
        # Фильтруем профили
        suitable_profiles = []
        
        for uid, profile in profiles.items():
            user_id_int = int(uid)
            
            # Пропускаем исключенного пользователя
            if exclude_user_id and user_id_int == exclude_user_id:
                continue
            
            # Проверяем активность
            if not profile.get('is_active', True):
                continue
            
            # Применяем фильтры
            matches_filters = True
            
            if filters:
                # Фильтр по городу
                if filters.get('city'):
                    profile_city = profile.get('city', '').lower().strip()
                    filter_city = filters['city'].lower().strip()
                    if profile_city != filter_city:
                        matches_filters = False
                
                # Фильтр по полу (ищем частичное совпадение)
                if matches_filters and filters.get('gender'):
                    target_gender = filters['gender'].lower()
                    profile_gender = profile.get('gender', '').lower()
                    
                    # Ищем ключевые слова в поле пола
                    if "девушка" in target_gender and "девушка" not in profile_gender:
                        matches_filters = False
                    elif "парень" in target_gender and "парень" not in profile_gender:
                        matches_filters = False
            
            if matches_filters:
                # Добавляем user_id в профиль
                profile['user_id'] = user_id_int
                suitable_profiles.append(profile)
        
        print(f"🔍 Найдено подходящих профилей: {len(suitable_profiles)}")
        
        if not suitable_profiles:
            return None
        
        # Выбираем случайный профиль
        selected_profile = random.choice(suitable_profiles)
        print(f"🎯 Выбран профиль: {selected_profile.get('name')} (ID: {selected_profile['user_id']})")
        
        return selected_profile
    
    def add_like(self, from_user_id: int, to_user_id: int) -> bool:
        """Добавляет лайк"""
        data = self._load_data()
        
        if 'likes' not in data:
            data['likes'] = {}
        
        if str(from_user_id) not in data['likes']:
            data['likes'][str(from_user_id)] = []
        
        # Проверяем, не лайкал ли уже
        if str(to_user_id) not in data['likes'][str(from_user_id)]:
            data['likes'][str(from_user_id)].append(str(to_user_id))
        
        return self._save_data(data)
    
    def add_superlike(self, from_user_id: int, to_user_id: int, message: str) -> bool:
        """Добавляет суперлайк с сообщением"""
        data = self._load_data()
        
        if 'superlikes' not in data:
            data['superlikes'] = {}
        
        superlike_key = f"{from_user_id}_{to_user_id}"
        data['superlikes'][superlike_key] = {
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'message': message,
            'created_at': datetime.now().isoformat(),
            'is_read': False
        }
        
        # Также добавляем обычный лайк
        self.add_like(from_user_id, to_user_id)
        
        return self._save_data(data)
    
    def add_report(self, from_user_id: int, to_user_id: int, reason: str = None) -> bool:
        """Добавляет жалобу на профиль"""
        data = self._load_data()
        
        if 'reports' not in data:
            data['reports'] = {}
        
        report_key = f"{from_user_id}_{to_user_id}_{datetime.now().timestamp()}"
        data['reports'][report_key] = {
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'reason': reason,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        return self._save_data(data)
    
    def check_mutual_like(self, user1_id: int, user2_id: int) -> bool:
        """Проверяет взаимный лайк"""
        data = self._load_data()
        
        likes1 = data['likes'].get(str(user1_id), [])
        likes2 = data['likes'].get(str(user2_id), [])
        
        return str(user2_id) in likes1 and str(user1_id) in likes2
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получает статистику пользователя"""
        data = self._load_data()
        
        likes_received = 0
        likes_given = 0
        mutual_likes = 0
        
        # Считаем полученные лайки
        for uid, liked_users in data.get('likes', {}).items():
            if str(user_id) in liked_users:
                likes_received += 1
        
        # Считаем отправленные лайки
        likes_given = len(data.get('likes', {}).get(str(user_id), []))
        
        # Считаем взаимные лайки
        for uid, liked_users in data.get('likes', {}).items():
            if uid != str(user_id) and str(user_id) in liked_users:
                if str(uid) in data.get('likes', {}).get(str(user_id), []):
                    mutual_likes += 1
        
        return {
            'likes_received': likes_received,
            'likes_given': likes_given,
            'mutual_likes': mutual_likes
        }
    
    def get_unread_superlikes(self, user_id: int) -> List[Dict]:
        """Получает непрочитанные суперлайки пользователя"""
        data = self._load_data()
        unread_superlikes = []
        
        for superlike_key, superlike_data in data.get('superlikes', {}).items():
            if (superlike_data['to_user_id'] == user_id and 
                not superlike_data.get('is_read', False)):
                unread_superlikes.append(superlike_data)
        
        return unread_superlikes
    
    def mark_superlike_read(self, from_user_id: int, to_user_id: int) -> bool:
        """Отмечает суперлайк как прочитанный"""
        data = self._load_data()
        
        superlike_key = f"{from_user_id}_{to_user_id}"
        if superlike_key in data.get('superlikes', {}):
            data['superlikes'][superlike_key]['is_read'] = True
            return self._save_data(data)
        
        return False
    
    def update_profile_status(self, user_id: int, is_active: bool) -> bool:
        """Обновляет статус активности профиля"""
        data = self._load_data()
        
        if str(user_id) in data['profiles']:
            data['profiles'][str(user_id)]['is_active'] = is_active
            data['profiles'][str(user_id)]['last_updated'] = datetime.now().isoformat()
            return self._save_data(data)
        
        return False

# Глобальный экземпляр базы данных
db = JSONDatabase()
