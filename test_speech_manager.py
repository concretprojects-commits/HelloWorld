import unittest
from speech_manager import SpeechManager, VoiceRole

class TestSpeechManager(unittest.TestCase):
    def setUp(self):
        self.speech = SpeechManager()

    def test_voice_change(self):
        self.assertTrue(self.speech.change_voice('female') or self.speech.change_voice('male'))

    def test_adjust_speech(self):
        self.speech.adjust_speech(rate=200, volume=0.5)
        # No assertion, just ensure no error

    def test_language_change(self):
        self.assertTrue(self.speech.change_language('en'))
        self.assertTrue(self.speech.change_language('es'))
        self.assertFalse(self.speech.change_language('xx'))

    def test_play_sound_effect(self):
        self.speech.play_sound_effect('notification')
        self.speech.play_sound_effect('error')
        self.speech.play_sound_effect('success')

    def test_speak(self):
        self.speech.speak("Testing speech output", VoiceRole.GENERAL)
        self.speech.speak("Prueba de voz", VoiceRole.GENERAL)

    def tearDown(self):
        self.speech.cleanup()

if __name__ == '__main__':
    unittest.main()
