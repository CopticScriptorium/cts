import meilisearch

class Search():
    def __init__(self):
        self.client = meilisearch.Client('http://127.0.0.1:7700', 'masterKey')
        self.index="texts"
        self.client.create_index(self.index, {'primaryKey': 'id'})
        pass
    
    def index_text(self, texts):
        return self.client.index(self.index).add_documents(texts)
    
    def search(self, keyword):
        return self.client.index(self.index).search(keyword)

    def transliterate_to_coptic(input_text):
        """
        Transliterates a given text from qwerty-based input to Coptic, with priority
        for double-letter replacements before single-letter replacements.
        """
        # Priority: Double-letter replacements
        double_letter_map = {
            "th": "Ⲑ",  # Theta
            "kh": "Ⲭ",  # Khi
            "ps": "Ⲯ",  # Psi
            "sh": "Ϣ",  # Shei
        }

        # Single-letter replacements
        single_letter_map = {
            "a": "Ⲁ",  # Alpha
            "b": "Ⲃ",  # Beta
            "g": "Ⲅ",  # Gamma
            "d": "Ⲇ",  # Dalda
            "e": "Ⲉ",  # Ei
            "z": "Ⲍ",  # Zeta
            "h": "Ⲏ",  # Eta
            "i": "Ⲓ",  # Iota
            "k": "Ⲕ",  # Kappa
            "l": "Ⲗ",  # Laula
            "m": "Ⲙ",  # Mi
            "n": "Ⲛ",  # Ni
            "x": "Ⲝ",  # Ksi
            "o": "Ⲟ",  # O
            "p": "Ⲡ",  # Pi
            "r": "Ⲣ",  # Ro
            "s": "Ⲥ",  # Sigma
            "t": "Ⲧ",  # Tau
            "u": "Ⲩ",  # Upsilon
            "f": "Ϥ",  # Fi
            "q": "Ϩ",  # Hori
            "w": "Ⲱ",  # Omega
        }

        # Step 1: Replace double-letter sequences
        for double, coptic in double_letter_map.items():
            input_text = input_text.replace(double, coptic)

        # Step 2: Replace single letters
        for single, coptic in single_letter_map.items():
            input_text = input_text.replace(single, coptic)

        return input_text