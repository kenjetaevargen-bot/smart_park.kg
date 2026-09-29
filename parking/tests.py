from django.test import TestCase

from parking.models import UserProfile


class AuthFlowTests(TestCase):
    def test_login_existing_user_sets_session(self):
        user = UserProfile.objects.create(
            name="Алина",
            surname="Курманова",
            phone="+996700123456",
            email="alina@example.com",
        )

        response = self.client.post(
            "/api/login/",
            {"phone_or_email": "+996700123456"},
            follow=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["user_profile_id"], user.id)
        self.assertIn("account", response.json())

    def test_logout_clears_current_account(self):
        user = UserProfile.objects.create(
            name="Бек",
            surname="Тилеков",
            phone="+996555111222",
            email="bek@example.com",
        )
        session = self.client.session
        session["user_profile_id"] = user.id
        session.save()

        response = self.client.post("/api/logout/", follow=False)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("user_profile_id", self.client.session)
        self.assertTrue(response.json()["ok"])
