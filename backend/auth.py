# Login, password, user account management


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
        ok = bool(self.exec(
            "UPDATE users SET must_change_password=0 WHERE email=%s", (email,)))
        if ok:
            self.log_activity("Edited", "User", f"Cleared must_change_password for {email}")
        return ok

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

    # ── User Account Management (Admin) ────────────────────────────
    def get_all_user_accounts(self):
        return self.fetch("""
            SELECT u.user_id, u.full_name, u.email, r.role_name,
                   COALESCE(u.must_change_password, 0) AS must_change_password
            FROM users u INNER JOIN roles r ON u.role_id = r.role_id
            ORDER BY u.user_id
        """, ())

    def admin_create_user_account(self, full_name, email, password, role_name):
        try:
            role = self.fetch("SELECT role_id FROM roles WHERE role_name=%s", (role_name,), one=True)
            if not role:
                return False, f"Role '{role_name}' not found."
            existing = self.fetch("SELECT user_id FROM users WHERE email=%s", (email,), one=True)
            if existing:
                return False, f"A user with email '{email}' already exists."
            ok = self.exec(
                "INSERT INTO users (full_name, email, password, role_id, must_change_password) VALUES (%s,%s,%s,%s,1)",
                (full_name, email, password, role["role_id"]))
            if ok:
                self.log_activity("Created", "User", f"Account created for {full_name} ({role_name})")
                return True, f"Account for '{full_name}' created.\nThey must change their password on first login."
            return False, "Failed to create account."
        except Exception as e:
            return False, f"Error: {e}"

    def admin_reset_password(self, user_id, new_password):
        try:
            ok = self.exec(
                "UPDATE users SET password=%s, must_change_password=1 WHERE user_id=%s",
                (new_password, user_id))
            if ok:
                self.log_activity("Edited", "User", f"Password reset for user #{user_id}")
                return True, "Password reset. User must change it on next login."
            return False, "Failed to reset password."
        except Exception as e:
            return False, f"Error: {e}"

    def admin_delete_user_account(self, user_id):
        try:
            ok = self.exec("DELETE FROM users WHERE user_id=%s", (user_id,))
            if ok:
                self.log_activity("Deleted", "User", f"User account #{user_id} deleted")
                return True, "User account deleted."
            return False, "Failed to delete account."
        except Exception as e:
            return False, f"Error: {e}"

    # ── Helpers ────────────────────────────────────────────────────

    def force_change_password(self, email, new_pw):
        """Set a new password and clear the must_change_password flag."""
        ok = bool(self.exec(
            "UPDATE users SET password=%s, must_change_password=0 WHERE email=%s",
            (new_pw, email)))
        if ok:
            self.log_activity("Edited", "User", f"Password changed (first login) for {email}")
        return ok

    def get_user_full_name(self, email):
        """Return the full_name for a user, or None."""
        row = self.fetch(
            "SELECT full_name FROM users WHERE email=%s", (email,), one=True)
        return row["full_name"] if row else None

    def get_all_roles(self):
        """Return a list of role name strings."""
        rows = self.fetch(
            "SELECT role_name FROM roles ORDER BY role_id", ())
        return [r["role_name"] for r in (rows or [])]
