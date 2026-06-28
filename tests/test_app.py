import unittest

from app import app


class SteamStoreTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_owned_game_cannot_be_bought_again(self):
        with self.client.session_transaction() as session:
            session["wallet"] = 100.0
            session["library"] = [1]

        response = self.client.get("/checkout/1", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/library")

    def test_add_to_cart_stores_game_in_session(self):
        with self.client.session_transaction() as session:
            session["wallet"] = 100.0
            session["username"] = "tester"
            session["library"] = []
            session["cart"] = []

        response = self.client.post("/add_to_cart/1", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Added to cart", response.get_data(as_text=True))

        with self.client.session_transaction() as session:
            self.assertEqual(session["cart"], [1])


if __name__ == "__main__":
    unittest.main()
