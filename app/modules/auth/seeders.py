from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.seeders.BaseSeeder import BaseSeeder


class AuthSeeder(BaseSeeder):

    priority = 1  # Higher priority

    def run(self):

        # Seeding users
        # Only create users if they do not already exist to avoid duplicate key errors
        users_to_create = []
        for email in ("user1@example.com", "user2@example.com"):
            existing = User.query.filter_by(email=email).first()
            if not existing:
                users_to_create.append(User(email=email, password="1234"))

        if users_to_create:
            # Inserted users with their assigned IDs are returned by `self.seed`.
            seeded_users = self.seed(users_to_create)
        else:
            # If no new users were created, fetch the existing ones to create profiles later
            seeded_users = []
            for email in ("user1@example.com", "user2@example.com"):
                seeded_users.append(User.query.filter_by(email=email).first())

        # Create profiles for each user inserted.
        user_profiles = []
        names = [("John", "Doe"), ("Jane", "Doe")]

        for user, name in zip(seeded_users, names):
            profile_data = {
                "user_id": user.id,
                "orcid": "",
                "affiliation": "Some University",
                "name": name[0],
                "surname": name[1],
            }
            user_profile = UserProfile(**profile_data)
            user_profiles.append(user_profile)

        # Seeding user profiles
        self.seed(user_profiles)
