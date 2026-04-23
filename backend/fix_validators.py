import re

with open('core/input_validation.py', encoding='utf-8') as f:
    content = f.read()

# sanitize_url metodu ekle (validate_url'dan once)
url_pattern = r'(@staticmethod\s+def validate_url\(url: str\) -> bool:.*?return True)'
url_replacement = '''@staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize and validate URL - only allow http/https"""
        if not url or not isinstance(url, str):
            raise InputValidationError('Invalid URL: empty or not string')
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            raise InputValidationError(f'Invalid URL scheme: {url}')
        return url
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL - returns bool for backward compatibility"""
        try:
            SecurityValidator.sanitize_url(url)
            return True
        except InputValidationError:
            return False'''

content = re.sub(url_pattern, url_replacement, content, flags=re.DOTALL)

# sanitize_integer metodu ekle
int_pattern = r'(@staticmethod\s+def validate_integer\(value, min_value: int = None, max_value: int = None\) -> bool:.*?return False)'
int_replacement = '''@staticmethod
    def sanitize_integer(value, min_value: int = None, max_value: int = None) -> int:
        """Sanitize and validate integer with optional range"""
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise InputValidationError(f'Invalid integer: {value}')
        if min_value is not None and int_val < min_value:
            raise InputValidationError(f'Integer {int_val} below minimum {min_value}')
        if max_value is not None and int_val > max_value:
            raise InputValidationError(f'Integer {int_val} above maximum {max_value}')
        return int_val
    
    @staticmethod
    def validate_integer(value, min_value: int = None, max_value: int = None) -> bool:
        """Validate integer - returns bool for backward compatibility"""
        try:
            SecurityValidator.sanitize_integer(value, min_value, max_value)
            return True
        except InputValidationError:
            return False'''

content = re.sub(int_pattern, int_replacement, content, flags=re.DOTALL)

# sanitize_float metodu ekle
float_pattern = r'(@staticmethod\s+def validate_float\(value\) -> bool:.*?return False\s+)'
float_replacement = '''@staticmethod
    def sanitize_float(value) -> float:
        """Sanitize and validate float - reject inf and nan"""
        try:
            float_val = float(value)
        except (ValueError, TypeError):
            raise InputValidationError(f'Invalid float: {value}')
        if float_val != float_val:  # nan check
            raise InputValidationError('Float cannot be NaN')
        if float_val == float('inf') or float_val == float('-inf'):
            raise InputValidationError('Float cannot be infinite')
        return float_val
    
    @staticmethod
    def validate_float(value) -> bool:
        """Validate float - returns bool for backward compatibility"""
        try:
            SecurityValidator.sanitize_float(value)
            return True
        except InputValidationError:
            return False
    
    '''

content = re.sub(float_pattern, float_replacement, content, flags=re.DOTALL)

with open('core/input_validation.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - Metodlar guncellendi')
