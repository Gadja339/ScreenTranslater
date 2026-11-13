import requests
from PySide6.QtCore import QObject, Signal, Slot
from word2word import Word2word
from pathlib import Path


class TranslateWorker(QObject):

    result = Signal(str, str)
    error = Signal(str, str)

    def __init__(self):
        super().__init__()

        self.dictionary = None

    @Slot(str)
    def translate(self, word):
        try:
            # Загружаем словарь только один раз
            if self.dictionary is None:

                savedir = (
                    Path.home()
                    / ".screentranslate"
                    / "word2word"
                )

                self.dictionary = Word2word(
                    "en",
                    "ru",
                    custom_savedir=str(savedir)
                )

            # Получаем три варианта перевода
            translations = self.dictionary(
                word.lower().strip(),
                n_best=3
            )

            if not translations:
                raise LookupError("Переводы отсутствуют")

            # Превращаем список в строку
            translation = ", ".join(translations)

            self.result.emit(word, translation)

        except KeyError:
            self.error.emit(
                word,
                "Слово отсутствует в словаре"
            )

        except Exception as e:
            self.error.emit(word, str(e))