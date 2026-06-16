import hashlib

class TextShortener:
    def __init__(self):
        # Base62 character set: 10 digits + 26 lowercase + 26 uppercase
        self.chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.base = len(self.chars)

    def _text_to_number(self, text: str) -> int:
        """Hashes text into a large, consistent integer."""
        # MD5 creates a deterministic 128-bit hash
        hash_hex = hashlib.md5(text.encode('utf-8')).hexdigest()
        return int(hash_hex, 16)

    def shorten(self, text: str, max_length: int = 6) -> str:
        """Converts text into a short string under the max_length limit."""
        num = self._text_to_number(text)
        short_str = ""
        
        # Convert the number to Base62
        while num > 0:
            num, remainder = divmod(num, self.base)
            short_str = self.chars[remainder] + short_str
            
        # Slice to the requested length (e.g., 6 characters)
        return short_str[:max_length]
    
"""
# --- Usage Example ---
shortener = TextShortener()

text1 = "Google.com"
text2 = "An incredibly long piece of text that needs shortening."

print(f"{text1} -> {shortener.shorten(text1)}")
print(f"{text2} -> {shortener.shorten(text2)}")

"""