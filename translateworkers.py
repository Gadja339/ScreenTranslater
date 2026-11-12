import requests
from PySide6.QtCore import QObject, Signal, Slot

class TranslateWorker(QObject):

    result = Signal(str, str)
    error = Signal(str, str)

    @Slot(str)
    def translate(self, word):
        try:
            response = requests.get(
                "https://api.mymemory.translated.net/get",
                params={
                    "q": word,
                    "langpair": "en|ru"
                },
                timeout=5
            )

            response.raise_for_status()
            data = response.json()

            if data.get("responseStatus") != 200:
                raise ValueError(
                    data.get("responseDetails")
                    or "Translation API error"
                )

            translation = data["responseData"]["translatedText"]

            self.result.emit(word, translation)

        except Exception as e:
            self.error.emit(word, str(e))