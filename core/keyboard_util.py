import random

class KeyboardLayouts:
    # Türkçe Q Klavye Komşu Tuş Haritası
    TR_Q = {
        'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'ı': 'uokj', 'o': 'ılpk', 'p': 'oğöl',
        'a': 'sqz', 's': 'axdew', 'd': 'scfrke', 'f': 'dvgrt', 'g': 'fbhty', 'h': 'gnjyu', 'j': 'hkmıu', 'k': 'jlmıo', 'l': 'kşöp',
        'z': 'asx', 'x': 'zsdc', 'c': 'xvdf', 'v': 'cbfg', 'b': 'vngh', 'n': 'bmhj', 'm': 'njk'
    }

    # İngilizce QWERTY Klavye Komşu Tuş Haritası
    EN_Q = {
        'q': 'wa', 'w': 'qeas', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg', 'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'ilpk', 'p': 'ol',
        'a': 'sqz', 's': 'axdew', 'd': 'scfret', 'f': 'dvgrt', 'g': 'fbhty', 'h': 'gnjyu', 'j': 'hkmui', 'k': 'jliuo', 'l': 'kop',
        'z': 'asx', 'x': 'zsdc', 'c': 'xvdf', 'v': 'cbfg', 'b': 'vngh', 'n': 'bmhj', 'm': 'njk'
    }

    @staticmethod
    def get_nearby_char(char, lang='tr'):
        layout = KeyboardLayouts.TR_Q if lang == 'tr' else KeyboardLayouts.EN_Q
        neighbors = layout.get(char.lower(), 'x')
        return random.choice(neighbors)