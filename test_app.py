import unittest
from unittest.mock import MagicMock, patch
import json
from psycopg.errors import UniqueViolation
from app import app, cache

class TinyURLApiTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the Flask test client and clear the cache before every test."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Clear the server-side memory cache between test runs
        with app.app_context():
            cache.clear()

    @patch('app.DatabaseProvider')
    def test_create_url_missing_long_url(self, mock_db_class):
        """Verify endpoint rejects payloads missing the required longUrl field."""
        response = self.app.post('/tiny-url/create', json={"customAlias": "test"})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required field", data["error"])

    @patch('app.DatabaseProvider')
    def test_create_custom_url_success(self, mock_db_class):
        """Verify successful short URL creation when custom alias is available."""
        mock_db_instance = mock_db_class.return_value
        # Mock successful insert (no exception thrown)
        mock_db_instance.insert_sample_url.return_value = None

        payload = {"longUrl": "https://example.com", "customAlias": "my-promo"}
        response = self.app.post('/tiny-url/create', json=payload)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        self.assertIn("/redirect/my-promo", data["shortUrl"])
        # Ensure the DB insert was attempted with the cleaned alias
        mock_db_instance.insert_sample_url.assert_called_once()

    @patch('app.DatabaseProvider')
    def test_create_custom_url_race_condition(self, mock_db_class):
        """Verify a 409 Conflict is returned when Postgres hits a UniqueViolation constraint."""
        mock_db_instance = mock_db_class.return_value
        # Simulate Postgres catching a race condition or duplicate key conflict
        mock_db_instance.insert_sample_url.side_effect = UniqueViolation("Duplicate key error")

        payload = {"longUrl": "https://example.com", "customAlias": "taken-alias"}
        response = self.app.post('/tiny-url/create', json=payload)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(data["error"], "Custom alias already exists")

    @patch('app.DatabaseProvider')
    def test_redirect_not_found(self, mock_db_class):
        """Verify a 404 response when requesting an alias that does not exist in DB."""
        mock_db_instance = mock_db_class.return_value
        mock_db_instance.find_url_metadata.return_value = None

        response = self.app.get('/redirect/missing-alias')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "URL not found")

    @patch('app.DatabaseProvider')
    def test_redirect_caching_and_hit(self, mock_db_class):
        """Verify the endpoint caches metadata and avoids secondary database reads."""
        mock_db_instance = mock_db_class.return_value
        mock_db_instance.find_url_metadata.return_value = {"long_url": "https://target-destination.com"}

        # --- Request 1: Cache Miss ---
        # This first request must hit the database to retrieve the mapping
        response1 = self.app.get('/redirect/cached-alias')
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.headers['Location'], "https://target-destination.com")
        self.assertEqual(mock_db_instance.find_url_metadata.call_count, 1)

        mock_db_instance.reset_mock()
        
        # --- Request 2: Cache Hit ---
        # Reset the mock tracker to observe fresh behavior on request two
        mock_db_instance.find_url_metadata.reset_mock()
        
        response2 = self.app.get('/redirect/cached-alias')
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(response2.headers['Location'], "https://target-destination.com")
        
        # Core assertion: Metadata read must be 0 because it was pulled from cache
        mock_db_instance.find_url_metadata.assert_not_called()
        # Analytics counter must still execute regardless of cache hit status
        mock_db_instance.increment_access_count.assert_called_once_with('cached-alias')

if __name__ == '__main__':
    unittest.main()
