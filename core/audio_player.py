from pathlib import Path

from pydub import AudioSegment
from pydub import playback

from core.di import container
from core.system_events.types import SystemEvent, SystemEventAppError


class AudioPlayer:
    """
    Занимается воспроизведением аудио
    """

    @classmethod
    def play(cls, file_path: Path | str, volume_offset: int = 0):
        _file_path = Path(file_path)
        try:
            audio_object = cls._get_pydub_audio_segment(_file_path, volume_offset)
            playback.play(audio_object)
        except Exception as e:
            event_bus = container.event_bus
            event_bus.publish(
                SystemEvent(
                    type='error.system',
                    data=SystemEventAppError(
                        source='AudioPlayer',
                        error=f'Ошибка воспроизведения аудио: {_file_path}',
                    )
                )
            )

    @staticmethod
    def _get_pydub_audio_segment(file_path: Path, volume_offset: int) -> AudioSegment:
        if file_path.suffix == '.mp3':
            audio_object = AudioSegment.from_mp3(file_path)
        elif file_path.suffix == '.wav':
            audio_object = AudioSegment.from_wav(file_path)
        else:
            audio_object = AudioSegment.from_file(file_path)

        return audio_object + volume_offset
