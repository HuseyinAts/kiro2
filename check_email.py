try:
    import email_validator
    with open("email_check.txt", "w") as f:
        f.write(f"OK: email-validator {email_validator.__version__}")
except ImportError as e:
    with open("email_check.txt", "w") as f:
        f.write(f"FAIL: {e}")
