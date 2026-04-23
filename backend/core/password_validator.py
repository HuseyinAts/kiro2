"""
Strong Password Validation
SECURITY FIX: Enforce password complexity requirements
"""
import re

# Common passwords to reject (top 100 most common)
COMMON_PASSWORDS = {
    "password",
    "123456",
    "12345678",
    "qwerty",
    "abc123",
    "monkey",
    "1234567",
    "letmein",
    "trustno1",
    "dragon",
    "baseball",
    "iloveyou",
    "master",
    "sunshine",
    "ashley",
    "bailey",
    "passw0rd",
    "shadow",
    "123123",
    "654321",
    "superman",
    "qazwsx",
    "michael",
    "football",
    "password1",
    "welcome",
    "jesus",
    "ninja",
    "mustang",
    "password123",
    "admin",
    "admin123",
    "root",
    "toor",
    "pass",
    "test",
    "guest",
    "info",
    "adm",
    "mysql",
    "user",
    "administrator",
    "oracle",
    "ftp",
    "pi",
    "puppet",
    "ansible",
    "ec2-user",
    "vagrant",
    "azureuser",
    "sifre",
    "parola",
    "12345",
    "123456789",
    "qwerty123",
    "ankara",
    "istanbul",
    "trabzon",
    "galatasaray",
    "fenerbahce",
    "besiktas",
    "turkiye",
    "merhaba",
}


class PasswordValidationError(Exception):
    """Custom exception for password validation failures"""



class PasswordValidator:
    """
    Strong password policy validator

    Requirements:
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    - Not in common passwords list
    - Not contain sequential characters (abc, 123)
    """

    MIN_LENGTH = 12
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str, username: str | None = None) -> None:
        """
        Validate password against all requirements

        Args:
            password: Password to validate
            username: Optional username to check for similarity

        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        errors: list[str] = []

        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")

        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must be at most {cls.MAX_LENGTH} characters long")

        # Uppercase check
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        # Lowercase check
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        # Digit check
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        # Special character check
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
            errors.append(
                'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\\\\/~`)'
            )

        # Common password check (case-insensitive)
        if password.lower() in COMMON_PASSWORDS:
            errors.append(
                "Password is too common. Please choose a more unique password"
            )

        # Sequential characters check
        if cls._has_sequential_characters(password):
            errors.append("Password contains sequential characters (e.g., abc, 123)")

        # Username similarity check
        if username and cls._is_similar_to_username(password, username):
            errors.append("Password is too similar to username")

        # Repeated characters check
        if cls._has_repeated_characters(password):
            errors.append("Password contains too many repeated characters")

        # Raise all errors
        if errors:
            raise PasswordValidationError("; ".join(errors))

    @staticmethod
    def _has_sequential_characters(password: str, min_sequence_length: int = 3) -> bool:
        """Check for sequential characters like 'abc' or '123'"""
        password_lower = password.lower()

        # Check for sequential letters
        for i in range(len(password_lower) - min_sequence_length + 1):
            sequence = password_lower[i : i + min_sequence_length]
            if all(
                ord(sequence[j]) + 1 == ord(sequence[j + 1])
                for j in range(len(sequence) - 1)
            ):
                return True
            if all(
                ord(sequence[j]) - 1 == ord(sequence[j + 1])
                for j in range(len(sequence) - 1)
            ):
                return True

        # Check for sequential digits
        for i in range(len(password) - min_sequence_length + 1):
            sequence = password[i : i + min_sequence_length]
            if sequence.isdigit():
                if all(
                    int(sequence[j]) + 1 == int(sequence[j + 1])
                    for j in range(len(sequence) - 1)
                ):
                    return True
                if all(
                    int(sequence[j]) - 1 == int(sequence[j + 1])
                    for j in range(len(sequence) - 1)
                ):
                    return True

        return False

    @staticmethod
    def _is_similar_to_username(password: str, username: str) -> bool:
        """Check if password is too similar to username"""
        password_lower = password.lower()
        username_lower = username.lower()

        # Exact match
        if password_lower == username_lower:
            return True

        # Username in password
        if username_lower in password_lower:
            return True

        # Password in username
        if password_lower in username_lower:
            return True

        # Reversed username
        if username_lower[::-1] in password_lower:
            return True

        return False

    @staticmethod
    def _has_repeated_characters(password: str, max_repeats: int = 3) -> bool:
        """Check for excessively repeated characters (e.g., 'aaaa')"""
        for i in range(len(password) - max_repeats):
            if all(password[i] == password[i + j] for j in range(max_repeats + 1)):
                return True
        return False

    @classmethod
    def get_strength_score(cls, password: str) -> int:
        """
        Calculate password strength score (0-100)

        Returns:
            int: Strength score where 100 is strongest
        """
        score = 0

        # Length bonus (up to 40 points)
        if len(password) >= cls.MIN_LENGTH:
            score += min(40, (len(password) - cls.MIN_LENGTH) * 2 + 20)

        # Character diversity (up to 40 points)
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(
            re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password)
        )

        score += sum([has_upper, has_lower, has_digit, has_special]) * 10

        # Uniqueness bonus (up to 20 points)
        if password.lower() not in COMMON_PASSWORDS:
            score += 10

        if not cls._has_sequential_characters(password):
            score += 5

        if not cls._has_repeated_characters(password):
            score += 5

        return min(100, score)

    @classmethod
    def get_strength_label(cls, password: str) -> str:
        """
        Get human-readable password strength label

        Returns:
            str: 'Weak', 'Fair', 'Good', 'Strong', or 'Very Strong'
        """
        score = cls.get_strength_score(password)

        if score < 40:
            return "Weak"
        if score < 60:
            return "Fair"
        if score < 80:
            return "Good"
        if score < 95:
            return "Strong"
        return "Very Strong"


# Convenience function for use in Pydantic models
def validate_password_strength(password: str, username: str | None = None) -> str:
    """
    Validate password and return it if valid

    Usage in Pydantic:
        password: str = Field(..., validator=validate_password_strength)
    """
    PasswordValidator.validate(password, username)
    return password
