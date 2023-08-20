class UserManager:
    def __init__(self):
        self.users = {}  # Dictionary to store user data

    def add_user(self, user_id, name, username, access_level):
        # Add a new user to the dictionary
        self.users[user_id] = {"name": name, "username": username, "access_level": access_level}

    def get_user_access_level(self, user_id):
        # Get the access level of a user
        if user_id in self.users:
            return self.users[user_id]["access_level"]
        else:
            return None

    def upgrade_access_level(self, user_id):
        # Upgrade the access level of a user (if applicable)
        if user_id in self.users:
            # Perform necessary checks and upgrades
            pass

    def downgrade_access_level(self, user_id):
        # Downgrade the access level of a user (if applicable)
        if user_id in self.users:
            # Perform necessary checks and downgrades
            pass

# Usage
user_manager = UserManager()
user_manager.add_user(user_id=123, name="John", username="john123", access_level="normal")

access_level = user_manager.get_user_access_level(123)
print(access_level)  # Output: "normal"

user_manager.upgrade_access_level(123)
