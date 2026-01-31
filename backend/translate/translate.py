import deep_translator

def translate_vietnamese(text, source_lang, target_lang):
    translator = deep_translator.Translator(from_lang=source_lang, to_lang=target_lang)
    translated_text = translator.translate(text)
    return translated_text
