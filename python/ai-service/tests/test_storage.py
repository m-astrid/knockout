"""
Tests for storage module.
"""
import os
import sys
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ["AI_SERVICE_DB_PATH"] = ":memory:"

from store import init_db, get_profile, save_profile, get_all_profiles, get_connection


class TestStorage(unittest.TestCase):
    """Сценарий: базовое хранилище профилей работает корректно"""
    
    def setUp(self):
        """Предусловия: БД инициализирована, пустая таблица профилей"""
        init_db()
        conn = get_connection()
        conn.execute("DELETE FROM profiles")
        conn.commit()
    
    def test_save_and_get_profile(self):
        """Сценарий: сохранение и получение профиля"""
        profile_link = "https://hemagon.com/users/test"
        target_dir = "/tmp/test_profile"
        files = ["profile.txt", "weapon_sabre.txt"]
        
        save_profile(profile_link, target_dir, files)
        
        result = get_profile(profile_link)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.profile_link, profile_link)
        self.assertEqual(result.target_dir, target_dir)
        self.assertEqual(result.files, files)
    
    def test_update_existing_profile(self):
        """Сценарий: обновление существующего профиля"""
        profile_link = "https://hemagon.com/users/test"
        
        save_profile(profile_link, "/tmp/dir1", ["file1.txt"])
        
        save_profile(profile_link, "/tmp/dir2", ["file2.txt"])
        
        result = get_profile(profile_link)
        
        self.assertEqual(result.target_dir, "/tmp/dir2")
        self.assertEqual(result.files, ["file2.txt"])
    
    def test_get_nonexistent_profile(self):
        """Сценарий: получение несуществующего профиля возвращает None"""
        result = get_profile("https://hemagon.com/users/nonexistent")
        
        self.assertIsNone(result)
    
    def test_get_all_profiles(self):
        """Сценарий: получение всех профилей"""
        save_profile("https://hemagon.com/users/user1", "/tmp/dir1", ["file1.txt"])
        save_profile("https://hemagon.com/users/user2", "/tmp/dir2", ["file2.txt"])
        
        results = get_all_profiles()
        
        self.assertEqual(len(results), 2)
        links = [r.profile_link for r in results]
        self.assertIn("https://hemagon.com/users/user1", links)
        self.assertIn("https://hemagon.com/users/user2", links)
    
    def test_files_stored_as_json(self):
        """Сценарий: список файлов сохраняется как JSON"""
        profile_link = "https://hemagon.com/users/test"
        files = ["a.txt", "b.txt", "c.txt"]
        
        save_profile(profile_link, "/tmp/dir", files)
        result = get_profile(profile_link)
        
        self.assertEqual(result.files, files)


if __name__ == "__main__":
    unittest.main()