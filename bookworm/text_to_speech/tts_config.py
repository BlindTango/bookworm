# coding: utf-8

import uuid
from pathlib import Path
from configobj import ConfigObj, ConfigObjError, ParseError
from validate import Validator, ValidateError
from bookworm import config
from bookworm.paths import config_path
from bookworm.concurrency import call_threaded


# Some useful constants
PARAGRAPH_PAUSE_MAX = 5000
END_OF_PAGE_PAUSE_MAX = 7000
END_OF_SECTION_PAUSE_MAX = 9000


class TTSConfigManager:
    """Manages configuration for the text-to-speech service."""

    def __init__(self):
        self._profile_path = Path(config_path()) / "voice_profiles"
        self.profiles = {}
        self.active_profile = None
        self.validator = Validator()
        if not self._profile_path.exists():
            self._profile_path.mkdir(parents=True)
            self._add_builtin_voice_profiles()
        self.list_voice_profiles()

    def list_voice_profiles(self):
        self.profiles.clear()
        if not self._profile_path.exists():
            self._profile_path.mkdir()
        for file in self._profile_path.iterdir():
            if file.suffix != ".ini":
                continue
            try:
                profile = self.load_voice_profile(str(file))
            except ConfigObjError:
                continue
            self.profiles[profile["name"]] = profile

    def create_voice_profile(self, name):
        if name in self.profiles:
            raise ValueError(f"A profile with the name {name} already exists.")
        filetoken = uuid.uuid5(uuid.NAMESPACE_X500, name)
        filename = self._profile_path / f"{filetoken}.ini"
        profile = self.load_voice_profile(str(filename))
        profile["name"] = name
        profile.write()
        return profile

    def load_voice_profile(self, filename):
        newspec = ConfigObj()
        newspec["name"] = 'string(default="")'
        newspec["speech"] = dict(tts_config_spec["speech"])
        profile = ConfigObj(
            infile=filename, configspec=newspec, create_empty=True, encoding="UTF8"
        )
        validated = profile.validate(self.validator)
        if validated:
            profile.write()
        return profile

    def delete_voice_profile(self, name):
        if name not in self.profiles:
            raise ValueError(f"Profile {name} does not exists.")
        profile_path = Path(self.profiles[name].filename)
        profile_path.unlink()

    def _add_builtin_voice_profiles(self):
        for pname, pdata in builtin_voice_profiles:
            profile = self.create_voice_profile(pname)
            profile["speech"].update(pdata)
            profile.write()

    def __getitem__(self, key):
        if self.active_profile is not None:
            return self.active_profile["speech"][key]
        return config.conf["speech"][key]

    def __setitem__(self, key, value):
        if self.active_profile is not None:
            self.active_profile[key] = value
        else:
            config.conf["speech"][key] = value

    def save(self):
        for profile in self.profiles.values():
            profile.write()
        config.save()


# Specs
tts_config_spec = {
    "reading": dict(
        use_continuous_reading="boolean(default=True)",
        # 0: entire book, 1: current section, 2: current_page
        reading_mode="integer(default=0, min=0, max=2)",
        # 0: from cursor position, 1: from beginning of page
        start_reading_from="integer(default=0, max=1, min=0)",
        speak_page_number="boolean(default=False)",
        highlight_spoken_text="boolean(default=True)",
        select_spoken_text="boolean(default=False)",
        play_end_of_section_sound="boolean(default=True)",
    ),
    "speech": dict(
        engine="string(default='sapi')",
        voice="string(default='')",
        rate="integer(default=50)",
        volume="integer(default=75)",
        sentence_pause=f"integer(default=0, min=0, max={PARAGRAPH_PAUSE_MAX})",
        paragraph_pause=f"integer(default=300, min=0, max={PARAGRAPH_PAUSE_MAX})",
        end_of_page_pause=f"integer(default=500, min=0, max={END_OF_PAGE_PAUSE_MAX})",
        end_of_section_pause=f"integer(default=900, min=0, max={END_OF_SECTION_PAUSE_MAX})",
    ),
}

builtin_voice_profiles = [
    (
        # Translators: the name of a built-in voice profile
        _("Human-like"),
        dict(
            rate=60,
            sentence_pause=250,
            paragraph_pause=500,
            end_of_page_pause=700,
            end_of_section_pause=900,
        ),
    ),
    (
        # Translators: the name of a built-in voice profile
        _("Deep Reading"),
        dict(
            rate=60,
            sentence_pause=400,
            paragraph_pause=800,
            end_of_page_pause=1000,
            end_of_section_pause=2500,
        ),
    ),
    (
        # Translators: the name of a built-in voice profile
        _("Expresse"),
        dict(
            rate=65,
            sentence_pause=0,
            paragraph_pause=300,
            end_of_page_pause=500,
            end_of_section_pause=700,
        ),
    ),
]
