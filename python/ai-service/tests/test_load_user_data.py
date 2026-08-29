"""
Tests for load_user_data module with storage integration.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ["AI_SERVICE_DB_PATH"] = ":memory:"

from store import init_db, get_profile, get_connection
from app.load_user_data import load_and_analyze
from app.read_user_data import AnalyzeResult


class TestLoadUserDataWithStorage(unittest.TestCase):
    """Сценарий: load_and_analyze использует storage для сохранения профилей"""
    
    def setUp(self):
        """Предусловия: БД инициализирована"""
        init_db()
        conn = get_connection()
        conn.execute("DELETE FROM profiles")
        conn.commit()
    
    @patch('app.load_user_data.requests.post')
    @patch('app.load_user_data.analyze_user_data')
    def test_saves_profile_to_storage(self, mock_analyze, mock_post):
        """Сценарий: после загрузки профиль сохраняется в storage"""
        mock_post.return_value.json.return_value = {"files_saved": ["profile.txt"]}
        mock_analyze.return_value = AnalyzeResult(profile={"name": "Test"})
        
        result = load_and_analyze(
            profile_link="https://hemagon.com/users/test",
            target_dir="/tmp/test_dir"
        )
        
        profile = get_profile("https://hemagon.com/users/test")
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.target_dir, "/tmp/test_dir")
        self.assertIn("result.json", profile.files)
    
    @patch('app.load_user_data.requests.post')
    @patch('app.load_user_data.analyze_user_data')
    def test_uses_existing_target_dir(self, mock_analyze, mock_post):
        """Сценарий: при повторном вызове используется существующий target_dir"""
        mock_post.return_value.json.return_value = {"files_saved": ["profile.txt"]}
        mock_analyze.return_value = AnalyzeResult(profile={"name": "Test"})
        
        load_and_analyze(
            profile_link="https://hemagon.com/users/test",
            target_dir="/tmp/test_dir"
        )
        
        mock_post.reset_mock()
        load_and_analyze(
            profile_link="https://hemagon.com/users/test"
        )
        
        call_args = mock_post.call_args[1]["json"]
        self.assertEqual(call_args["target_dir"], "/tmp/test_dir")


if __name__ == "__main__":
    unittest.main()