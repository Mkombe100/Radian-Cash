import unittest
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "server.py"

spec = importlib.util.spec_from_file_location("radian_server", SERVER_PATH)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class AuthHelpersTestCase(unittest.TestCase):
    def test_password_hash_and_verify(self):
        password = "Secret123!"
        hashed = server.hash_password(password)

        self.assertNotEqual(hashed, password)
        self.assertTrue(server.verify_password(password, hashed))
        self.assertFalse(server.verify_password("WrongPassword", hashed))

    def test_session_timeout_is_detected_after_threshold(self):
        recent_time = server.datetime.now(server.timezone.utc) - server.timedelta(minutes=10)
        expired_time = server.datetime.now(server.timezone.utc) - server.timedelta(minutes=31)

        self.assertFalse(server.is_session_expired(recent_time))
        self.assertTrue(server.is_session_expired(expired_time))


if __name__ == "__main__":
    unittest.main()
