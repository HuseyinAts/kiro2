import re


class BionicReadingConverter:
    """
    Faz 11: Nöro-Kapsayıcı (Neuro-Inclusive) İçerik Tasarımı
    DEHB ve Disleksi yaşayan öğrencilerin uzun paragraflarda kaybolmasını önlemek
    amacıyla kelimelerin odak (fixation) noktalarını kalınlaştırır.
    """

    @classmethod
    def convert_word(cls, word: str) -> str:
        """
        Tek bir kelimenin ilk hecelerini (veya belirli bir yüzdesini) kalınlaştırır.
        Noktalama işaretlerini korur.
        """
        if not word.strip():
            return word

        # Kelimenin başındaki ve sonundaki noktalama işaretlerini ayır
        match = re.match(r"^(\W*)([\wÇĞİÖŞÜçğıöşü]+)(\W*)$", word)
        if not match:
            # Sadece noktalama işareti veya sayı vs ise olduğu gibi dön
            return word

        prefix, core, suffix = match.groups()
        length = len(core)

        # Kelime uzunluğuna göre kalınlaştırılacak harf sayısını belirle
        # Genel kural: Yaklaşık %40-50 kalın (örneğin 5 harfli kelimede 2 harf, 7 harflide 3-4)
        if length == 1 or length <= 3:
            bold_count = 1
        elif length == 4:
            bold_count = 2
        else:
            # 5 harf ve üzeri için yarısından biraz azını (veya yarısını) al
            bold_count = max(2, int(length * 0.45))

        bold_part = core[:bold_count]
        rest = core[bold_count:]

        # HTML veya Markdown b etiketi ile sar
        return f"{prefix}<b>{bold_part}</b>{rest}{suffix}"

    @classmethod
    def convert_text(cls, text: str) -> str:
        """
        Verilen paragrafı bionic reading formatına çevirir.
        """
        if not text:
            return text

        # Satır sonlarını korumak için satır satır böl, kelimeleri çevir
        lines = text.split("\n")
        converted_lines = []

        for line in lines:
            words = line.split(" ")
            converted_words = [cls.convert_word(w) for w in words]
            converted_lines.append(" ".join(converted_words))

        return "\n".join(converted_lines)
