import logging
import re
from typing import ClassVar

logger = logging.getLogger(__name__)


class YKSJargonService:
    """
    Sesteş kelime ve YKS Jargonu izolasyon servisi.
    Bu servis, farklı disiplinlerde (örn: fizik, biyoloji, türkçe) farklı anlamlara gelen
    kelimelerin LLM tarafından yanlış bağlamda kullanılmasını (hallucination) önler.
    """

    # Kapalı devre sözlükler (Glossaries)
    # Farklı branşlardaki karmaşaları önlemek için genişletilmiş terim listesi
    SUBJECT_GLOSSARIES: ClassVar[dict[str, dict[str, str]]] = {
        "Fizik": {
            "iş": "Kuvvetin cisim üzerinde yol aldırarak enerji harcamasıdır (W=F.x). Günlük hayattaki 'iş, meslek, eylem, çalışma' anlamlarında KESİNLİKLE kullanılamaz.",
            "güç": "Birim zamanda yapılan iştir (P=W/t). 'Güçlü olmak, zorluk, kuvvet, iktidar' gibi mecazi anlamlarda kullanılamaz.",
            "enerji": "İş yapabilme yeteneğidir. 'Manevi enerji, sinerji, canlılık' bağlamında kullanılamaz.",
            "moment": "Kuvvetin döndürme etkisidir (Tork). 'An, zaman dilimi' anlamında kullanılamaz.",
            "basınç": "Birim yüzeye dik olarak etki eden kuvvettir. 'Psikolojik baskı, siyasi basınç' anlamında kullanılamaz.",
            "ivme": "Birim zamandaki hız değişimidir. 'Bir işin ivme kazanması, heyecanlanmak' anlamında kullanılamaz.",
            "yansıma": "Dalgaların (ışık, ses) bir yüzeye çarpıp geri dönmesidir. 'Düşüncelerin yansıması, toplumun yansıması' anlamında kullanılamaz.",
            "tepki": "Etkiye karşı oluşan zıt yönlü kuvvettir. 'İnsanların tepkisi, reaksiyon' anlamında kullanılamaz.",
            "kuvvet": "Cisimlerin hareket durumunu veya şeklini değiştiren etkidir. 'Siyasi kuvvet, devletin kuvveti' anlamında kullanılamaz.",
            "hız": "Birim zamandaki yer değiştirmedir. 'İnternet hızı, kalp atış hızı' gibi günlük bağlamlarda dikkatli kullanılmalı, vektörel olduğu (sürat ile farkı) gözetilmelidir.",
        },
        "Kimya": {
            "çözelti": "İki veya daha fazla maddenin oluşturduğu homojen karışımdır. Metaforik olarak 'bir problemin çözeltisi, çözüm' anlamında kullanılamaz.",
            "kök": "Birden fazla atomun bir araya gelerek oluşturduğu yüklü gruplardır (örn. Sülfat, Nitrat). Bitki kökü veya kelime kökü anlamında kullanılamaz.",
            "madde": "Kütlesi ve hacmi olan her şeydir. 'Anayasa maddesi, sözleşme maddesi, paragraf maddesi' anlamında kullanılamaz.",
            "hal": "Maddenin fiziksel durumudur (katı, sıvı, gaz). 'İnsanın hali, durum, tavır' anlamında kullanılamaz.",
            "tepkime": "Kimyasal reaksiyondur. 'Psikolojik tepki, insanların gösterdiği refleks' anlamında kullanılamaz.",
            "denge": "Kimyasal denge (ileri hız = geri hız). 'Ruhsal denge, terazi dengesi' gibi mecazi veya sadece fiziksel anlamlarda sınırlandırılamaz.",
            "saf": "İçinde yabancı madde bulunmayan maddedir (element, bileşik). 'Aptal, temiz niyetli, kolay kandırılan' anlamında kullanılamaz.",
            "asit": "Suda çözündüğünde H+ iyonu veren maddedir. 'Asitli içecek' bağlamında yüzeysel olarak geçiştirilemez, pH değeri kastedilmelidir.",
            "baz": "Suda çözündüğünde OH- iyonu veren maddedir. 'Baz almak (temel almak)' anlamında KESİNLİKLE kullanılamaz.",
            "alaşım": "İki veya daha fazla metalin (veya metal-ametal) homojen karışımıdır. 'Kültürlerin alaşımı, fikirlerin alaşımı' anlamında sosyolojik bağlamda kullanılamaz.",
        },
        "Biyoloji": {
            "kök": "Bitkilerde toprağa tutunan ve su/mineral alımını sağlayan organdır. Matematiksel denklem kökü veya dilbilgisel kök anlamında kullanılamaz.",
            "doku": "Aynı görevi yapmak üzere özelleşmiş hücre topluluğudur. 'Kumaş dokusu, metnin dokusu, his' anlamında kullanılamaz.",
            "hücre": "Canlının en küçük yapı taşıdır. 'Cezaevi hücresi, terör örgütü hücresi' anlamında kullanılamaz.",
            "adaptasyon": "Canlıların çevreye kalıtsal uyumudur. 'Senaryonun sinemaya adaptasyonu, okula adaptasyon' gibi sosyal anlamlarda kullanılamaz.",
            "canlı": "Hayat belirtisi gösteren organizmadır. 'Canlı renk, heyecanlı, dinamik ortam' anlamında kullanılamaz.",
            "hücre zarı": "Seçici geçirgen yapıdır. Mecazi olarak koruyucu kalkan anlamında genelleştirilemez.",
            "solunum": "Hücrelerin besinlerden ATP (enerji) elde etme sürecidir. Sadece 'nefes alıp verme' olarak basit bir şekilde tanımlanamaz.",
            "popülasyon": "Belli bir alanda yaşayan aynı tür canlıların oluşturduğu topluluktur. 'Dünya popülasyonu, seçmen popülasyonu' gibi genel demografik anlamlarda kullanılamaz.",
            "çevre": "Canlıların etkileşim içinde olduğu doğal veya fiziksel ortamdır. Geometrik şekil çevresi veya 'sosyal çevre' gibi diğer bağlamlarla karıştırılamaz.",
        },
        "Matematik": {
            "kök": "Bir denklemi sağlayan x değeridir veya karekök/küpkök ifadesidir. Biyolojik bitki kökü veya kelime kökü anlamında kullanılamaz.",
            "türev": "Bir fonksiyonun değişim oranı veya teğet eğimidir. 'Bu kelimenin türevi, ondan türemiş' gibi sözcüksel/dilbilimsel anlamlarda kullanılamaz.",
            "çarpan": "Bir sayıyı tam bölen veya çarpıldığında o sayıyı veren sayıdır. 'Dış çarpanlar, etkileyici faktörler' anlamında sosyal bağlamda kullanılamaz.",
            "oran": "İki çokluğun birbirine bölünmesidir. 'Orantısız güç, olayların oranı' gibi genel ifadeler yerine kesin matematiksel ilişki belirtmelidir.",
            "fonksiyon": "Tanım kümesindeki her elemanı değer kümesinde tek bir elemana eşleyen bağıntıdır. 'Bu aletin fonksiyonu (işlevi), görevi' anlamında kullanılamaz.",
            "limit": "Bir fonksiyonun belirli bir noktaya yaklaşırken aldığı değerdir. 'Kredi kartı limiti, sabır limiti' anlamında kullanılamaz.",
            "integral": "Eğri altında kalan alanı veya birikimli toplamı hesaplayan işlemdir. 'İntegral almak (bütünleştirmek)' şeklindeki sosyal veya felsefi anlamlarda kullanılamaz.",
        },
        "Türkçe": {
            "kök": "Bir kelimenin anlamlı en küçük parçasıdır. Matematiksel denklem kökü veya biyolojik bitki kökü anlamında kullanılamaz.",
            "gövde": "İsim veya fiil köklerine yapım eki getirilerek oluşturulan kelimedir. 'Ağaç gövdesi, insan gövdesi' şeklinde biyolojik anlamda kullanılamaz.",
            "ek": "Sözcüklere gelerek yeni anlam veya görev kazandıran hecelerdir. 'Rapora konulan ek, ilave, eklenti' anlamında kullanılamaz.",
            "fiil": "İş, oluş, hareket bildiren sözcüktür (eylem). 'Fiili olarak (gerçekte), fiiliyata dökmek' anlamında kullanılamaz.",
            "hece": "Bir nefes verişte çıkarılan ses veya ses grubudur. 'Bunu heceleyerek anlat (üstüne basa basa)' anlamında kullanılamaz.",
            "cümle": "Yargı bildiren kelime dizisidir. 'Cümle alem (herkes)' anlamındaki kalıplarla karıştırılmamalıdır.",
            "zarf": "Eylemin nasıllığını, zamanını veya miktarını belirten sözcüktür (belirteç). 'Mektup zarfı' anlamında kullanılamaz.",
            "sıfat": "İsmi niteleyen veya belirten sözcüktür (ön ad). 'Senin ne sıfatla (hangi hakla/ünvanla) konuştuğun' anlamında kullanılamaz.",
            "fiilimsi": "Fiilden türeyen ancak fiil çekimi almayan sözcüklerdir (eylemsi). Mecazi olarak 'harekete geçmeye meyilli' anlamında kullanılamaz.",
        },
        "Edebiyat": {
            "kök": "Bir kelimenin anlamlı en küçük parçasıdır. Matematiksel denklem kökü veya biyolojik bitki kökü anlamında kullanılamaz.",
            "gövde": "İsim veya fiil köklerine yapım eki getirilerek oluşturulan kelimedir. 'Ağaç gövdesi, insan gövdesi' şeklinde biyolojik anlamda kullanılamaz.",
            "vezin": "Şiirde hecelerin sayısına veya uzunluk-kısalığına dayanan ölçüdür. 'Vezinli (ölçülü) konuşmak' gibi mecazi kullanılmamalıdır.",
        },
        "Tarih": {
            "çağ": "Tarihte önemli bir olayla başlayıp başka bir önemli olayla biten zaman dilimidir. 'Günümüz çağı, internet çağı' gibi genel kültür tanımlarıyla YKS bağlamında karıştırılmamalıdır.",
            "devrim": "Mevcut düzenin zorla ve köklü biçimde yıkılarak yenisinin kurulmasıdır. 'Teknolojide devrim, devrim niteliğinde ürün' anlamında ticari/teknolojik kullanılmamalıdır.",
            "sınıf": "Tarihteki sosyal tabakalaşmadır (Asiller, köleler vb). 'Okul sınıfı, derslik' anlamında kullanılamaz.",
            "ıslahat": "Bozulan bir kurumu düzeltmek amacıyla yapılan iyileştirmedir. Modern tarım ıslahı veya evdeki tadilat anlamında kullanılamaz.",
            "fetih": "Bir ülkeyi veya şehri savaşarak ele geçirmedir. 'Gönülleri fethetmek' gibi duygusal anlamlarda kullanılamaz.",
        },
        "Coğrafya": {
            "iklim": "Geniş alanlarda uzun yıllar boyunca görülen hava olaylarının ortalamasıdır. 'Siyasi iklim, yatırım iklimi, okul iklimi' gibi mecazi anlamlarda kullanılamaz.",
            "bölge": "Doğal veya beşeri özellikler bakımından benzerlik gösteren alanlardır. 'Vücudun bel bölgesi, hastalıklı bölge' anlamında tıbbi bağlamda kullanılamaz.",
            "ölçek": "Haritadaki küçültme oranıdır. 'Büyük ölçekli iş, küçük ölçekli firma' gibi ticari anlamlarda kullanılamaz.",
            "fay": "Yer kabuğundaki kırıklardır. 'Arkadaşlar arasında fay hattı oluştu' (çatlak/ayrılık) anlamında kullanılamaz.",
            "nüfus": "Sınırları belirli bir alanda yaşayan insan sayısıdır. 'Nüfuz (etki alanı)' kelimesi ile KESİNLİKLE karıştırılamaz.",
            "cephe": "Farklı karakterdeki hava kütlelerinin karşılaşma alanıdır (sıcak cephe, soğuk cephe). Savaş cephesi veya bina cephesi anlamında kullanılamaz.",
        },
        "Geometri": {
            "doğru": "İki yönde sonsuza uzanan noktalar kümesidir. 'Gerçek, dürüstlük, haklı, mantıklı' anlamında ahlaki veya felsefi olarak kullanılamaz.",
            "açı": "Başlangıç noktaları aynı olan iki ışının birleşimidir. 'Benim açımdan, farklı bir açıdan bakmak' gibi fikir/perspektif anlamında kullanılamaz.",
            "çap": "Çember merkezinden geçen ve çemberi iki eş parçaya bölen kiriştir. 'O senin çapında biri değil, çaplı bir tartışma' anlamında kullanılamaz.",
            "nokta": "Boyutu olmayan tanımsız geometrik terimdir. 'Sözün bittiği nokta, son nokta, hassas nokta' anlamında kullanılamaz.",
            "düzlem": "Her yöne sonsuza kadar uzanan düz yüzeydir. 'Aynı düzlemde buluşmak, siyasi düzlem' gibi mecazi kullanılmamalıdır.",
            "çevre": "Bir çokgenin veya şeklin sınırlarının toplam uzunluğudur. 'Sosyal çevre, doğal çevre' anlamında biyolojik/sosyolojik olarak kullanılamaz.",
        },
    }

    @classmethod
    def get_jargon_prompt_injection(cls, subject: str) -> str:
        """
        Derse özel jargon kurallarını LLM promptuna enjekte edilecek XML formatında döner.
        Eğer o ders için bir sözlük tanımlı değilse boş string döner.
        """
        glossary = cls.SUBJECT_GLOSSARIES.get(subject)
        if not glossary:
            for key, val in cls.SUBJECT_GLOSSARIES.items():
                if key.lower() == subject.lower():
                    glossary = val
                    break

        if not glossary:
            return ""

        xml_parts = []
        xml_parts.append('<jargon_isolation priority="critical">')
        xml_parts.append(
            "  <instruction>Bu derse özgü teknik terimlerin (jargon) anlamları DİĞER DİSİPLİNLERDEN kesinlikle izole edilmelidir. Metaforik veya günlük kullanım YASAKTIR.</instruction>"
        )
        xml_parts.append("  <glossary>")

        for term, rule in glossary.items():
            xml_parts.append(f'    <term name="{term}">')
            xml_parts.append(f"      <rule>{rule}</rule>")
            xml_parts.append("    </term>")

        xml_parts.append("  </glossary>")
        xml_parts.append("</jargon_isolation>")

        return "\n".join(xml_parts)

    # PLR0912: her ders bloğu bağımsız, SUBJECT_GLOSSARIES ile aynı gruplamayı
    # yansıtıyor -- ayrı fonksiyonlara bölmek okunabilirliği azaltır.
    @classmethod
    def validate_text_jargon_compliance(cls, text: str, subject: str) -> list[str]:  # noqa: PLR0912
        """
        Soru metni veya çözümde istenmeyen/potansiyel sesteş ihlallerini basit regex yöntemiyle analiz eder.
        Gelişmiş NLP yerine Guardrail niteliğindedir.
        """
        warnings = []
        text_lower = text.lower()
        subject_lower = subject.lower()

        # BİYOLOJİ Kontrolleri
        if subject_lower == "biyoloji":
            if "kök" in text_lower and re.search(
                r"\b(denklem|karekök|küpkök|çözüm kümesi|kelime|hece)\b", text_lower
            ):
                warnings.append(
                    "Biyoloji sorusunda matematiksel veya dilbilgisi 'kök' ifadesi şüphesi."
                )
            if "doku" in text_lower and re.search(
                r"\b(kumaş|metin|his|içerik)\b", text_lower
            ):
                warnings.append(
                    "Biyoloji sorusunda metaforik 'doku' kelimesi kullanımı şüphesi."
                )
            if "hücre" in text_lower and re.search(
                r"\b(cezaevi|örgüt|hapis)\b", text_lower
            ):
                warnings.append(
                    "Biyoloji sorusunda gerçek dışı 'hücre' kelimesi kullanımı şüphesi."
                )
            if "çevre" in text_lower and re.search(
                r"\b(uzunluk|üçgen|kare|çember|çap|hesapla|cm)\b", text_lower
            ):
                warnings.append(
                    "Biyoloji sorusunda geometrik 'çevre' kelimesi kullanımı şüphesi."
                )

        # MATEMATİK & GEOMETRİ Kontrolleri
        if subject_lower in ["matematik", "geometri"]:
            if "kök" in text_lower and re.search(
                r"\b(bitki|toprak|gövde|yaprak|ağaç)\b", text_lower
            ):
                warnings.append(
                    "Matematik/Geometri sorusunda biyolojik 'kök' ifadesi şüphesi."
                )
            if "doğru" in text_lower and re.search(
                r"\b(dürüst|yalan|gerçek|haklı)\b", text_lower
            ):
                warnings.append(
                    "Matematik/Geometri sorusunda ahlaki 'doğru' kelimesi kullanımı şüphesi."
                )
            if "açı" in text_lower and re.search(
                r"\b(bakış|perspektif|düşünce)\b", text_lower
            ):
                warnings.append(
                    "Geometri sorusunda mecazi 'açı' kelimesi kullanımı şüphesi."
                )
            if "çevre" in text_lower and re.search(
                r"\b(doğa|doğal|sosyal|yaşam|toplum|insan)\b", text_lower
            ):
                warnings.append(
                    "Geometri sorusunda biyolojik/sosyal 'çevre' kelimesi kullanımı şüphesi."
                )

        # FİZİK Kontrolleri
        if subject_lower == "fizik":
            if "iş" in text_lower and re.search(
                r"\b(meslek|çalış|ofis|şirket|görev|istihdam)", text_lower
            ):
                warnings.append(
                    "Fizik sorusunda günlük 'iş' kelimesi kullanımı şüphesi."
                )
            if "güç" in text_lower and re.search(
                r"\b(zorluk|iktidar|yetenek|siyasi|askeri)\b", text_lower
            ):
                warnings.append("Fizik sorusunda mecazi 'güç' kullanımı şüphesi.")
            if "basınç" in text_lower and re.search(
                r"\b(psikolojik|siyasi|toplumsal|stres)\b", text_lower
            ):
                warnings.append("Fizik sorusunda mecazi 'basınç' kullanımı şüphesi.")

        # KİMYA Kontrolleri
        if subject_lower == "kimya":
            if "çözelti" in text_lower and re.search(
                r"\b(problem|mesele|sorun|toplumsal|kriz)\b", text_lower
            ):
                warnings.append(
                    "Kimya sorusunda metaforik 'çözelti' kelimesi kullanımı şüphesi."
                )
            if "madde" in text_lower and re.search(
                r"\b(anayasa|kanun|sözleşme|kural|metin)\b", text_lower
            ):
                warnings.append(
                    "Kimya sorusunda hukuksal 'madde' kelimesi kullanımı şüphesi."
                )
            if "saf" in text_lower and re.search(
                r"\b(aptal|kandırılan|kötülük|niyet|insan)\b", text_lower
            ):
                warnings.append(
                    "Kimya sorusunda sıfat olarak mecazi 'saf' kullanımı şüphesi."
                )
            if "alaşım" in text_lower and re.search(
                r"\b(kültür|sosyolojik|fikir|toplum|insan)\b", text_lower
            ):
                warnings.append(
                    "Kimya sorusunda sosyolojik bağlamda 'alaşım' kelimesi kullanımı şüphesi."
                )

        # TÜRKÇE & EDEBİYAT Kontrolleri
        if subject_lower in ["türkçe", "edebiyat"]:
            if "kök" in text_lower and re.search(
                r"\b(denklem|karekök|bitki|toprak)\b", text_lower
            ):
                warnings.append(
                    "Türkçe/Edebiyat sorusunda dilbilgisi dışı 'kök' ifadesi şüphesi."
                )
            if "cümle" in text_lower and re.search(r"\b(alem|herkes)\b", text_lower):
                warnings.append(
                    "Türkçe sorusunda kalıplaşmış mecazi 'cümle' kelimesi kullanımı şüphesi."
                )
            if "fiilimsi" in text_lower and re.search(
                r"\b(meyil|hareket|potansiyel|enerji|gibi)\b", text_lower
            ):
                warnings.append(
                    "Türkçe sorusunda mecazi 'fiilimsi' kelimesi kullanımı şüphesi."
                )

        # COĞRAFYA Kontrolleri
        if (
            subject_lower == "coğrafya"
            and "iklim" in text_lower
            and re.search(r"\b(siyasi|ekonomik|yatırım|ortam)\b", text_lower)
        ):
            warnings.append(
                "Coğrafya sorusunda mecazi 'iklim' kelimesi kullanımı şüphesi."
            )

        # TARİH Kontrolleri
        if (
            subject_lower == "tarih"
            and "devrim" in text_lower
            and re.search(r"\b(teknolojik|buluş|icat|ürün|şirket)\b", text_lower)
        ):
            warnings.append(
                "Tarih sorusunda ticari/teknolojik 'devrim' kelimesi kullanımı şüphesi."
            )

        return warnings
