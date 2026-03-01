# Login, dark mode, password stuff


class AuthMixin:

    def login(self, email, password):
        if not email:
            return False, "", "", "Please enter your email address."
        if not password:
            return False, "", "", "Please enter your password."
        try:
            user = self.fetch("""
                SELECT u.user_id, u.full_name, u.password, r.role_name,
                       COALESCE(u.must_change_password, 0) AS must_change_password
                FROM users u INNER JOIN roles r ON u.role_id = r.role_id
                WHERE u.email = %s
            """, (email,), one=True)
            if not user:
                return False, "", "", "No account found with that email."
            if user["password"] != password:
                return False, "", "", "Incorrect password."
            self.set_current_user(email, user["role_name"])
            self.log_activity("Login", "User", f"{user['full_name']} logged in")
            # Return must_change_password flag as 5th element
            return True, user["role_name"], user["full_name"], "Login successful.", bool(user["must_change_password"])
        except Exception as e:
            return False, "", "", f"Error: {e}", False

    def clear_must_change_password(self, email):
        """Clear the must_change_password flag after user changes their password."""
        return bool(self.exec(
            "UPDATE users SET must_change_password=0 WHERE email=%s", (email,)))

    def get_dark_mode(self, email):
        row = self.fetch("SELECT dark_mode FROM user_preferences WHERE user_email = %s", (email,), one=True)
        return bool(row["dark_mode"]) if row else False

    def set_dark_mode(self, email, enabled):
        return bool(self.exec("""
            INSERT INTO user_preferences (user_email, dark_mode) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE dark_mode = %s
        """, (email, int(enabled), int(enabled))))

    def update_own_password(self, email, current_pw, new_pw):
        user = self.fetch("SELECT password FROM users WHERE email = %s", (email,), one=True)
        if not user:
            return False, "User not found."
        if user["password"] != current_pw:
            return False, "Current password is incorrect."
        if self.exec("UPDATE users SET password = %s WHERE email = %s", (new_pw, email)):
            self.log_activity("Edited", "User", f"Password changed for {email}")
            return True, "Password updated successfully."
        return False, "Failed to update password."
