# coding: utf-8

import System
from System.Globalization import CultureInfo, CultureNotFoundException
from contextlib import suppress
from OcPromptBuilder import OcPromptBuilder
from bookworm.speech.enumerations import SpeechElementKind
from bookworm.speech.utterance import SpeechElement, SpeechStyle
from bookworm.logger import logger
from ..sapi.sp_utterance import SapiSpeechUtterance


log = logger.getChild(__name__)


class OcSpeechUtterance(SapiSpeechUtterance):
    def __init__(self, synth):
        super().__init__()
        self.synth = synth
        self._speech_sequence = []
        self._heal_funcs = []

    def start_paragraph(self):
        super().start_paragraph()
        self._heal_funcs.append((self.prompt.EndParagraph, ()))

    def start_style(self, style):
        super().start_style(style)
        self._heal_funcs.append((self.end_style, (style,)))

    def add_bookmark(self, bookmark):
        self._take_stock()
        self._speech_sequence.append(
            SpeechElement(SpeechElementKind.bookmark, bookmark)
        )

    def end_paragraph(self):
        with suppress(System.InvalidOperationException):
            super().end_paragraph()

    def end_style(self, style):
        with suppress(System.InvalidOperationException):
            super().end_style(style)

    def _take_stock(self):
        for func, args in self._heal_funcs:
            func(*args)
        self._heal_funcs.clear()
        voice = self.synth().voice
        voice_utterance = SapiSpeechUtterance()
        with voice_utterance.set_style(
            SpeechStyle(voice=voice, rate=self.synth().rate_to_spec())
        ):
            voice_utterance.append_utterance(self)
        voice_utterance.prompt.Culture = CultureInfo.GetCultureInfoByIetfLanguageTag(
            voice.language
        )
        ssml = voice_utterance.prompt.ToXml()
        if not self.prompt.IsEmpty:
            self.prompt.ClearContent()
        self._speech_sequence.append(SpeechElement(SpeechElementKind.ssml, ssml))

    def to_oc_prompt(self):
        oc_prompt = OcPromptBuilder()
        if not self.prompt.IsEmpty:
            self._take_stock()
        for element in self._speech_sequence:
            if element.kind is SpeechElementKind.ssml:
                oc_prompt.AddSsml(element.content)
            elif element.kind is SpeechElementKind.bookmark:
                oc_prompt.AddBookmark(element.content)
        return oc_prompt
