import unittest
from safety_quiz import SafetyQuizManager, SafetyQuestion
from speech_manager import SpeechManager, VoiceRole

class TestSafetyQuizManager(unittest.TestCase):
    def setUp(self):
        self.quiz = SafetyQuizManager()
        self.speech = SpeechManager()

    def test_get_random_question(self):
        question = self.quiz.get_random_question()
        self.assertIsInstance(question, SafetyQuestion)

    def test_check_answer(self):
        question = self.quiz.questions[0]
        correct, feedback = self.quiz.check_answer(question, question.correct_answer)
        self.assertTrue(correct)
        self.assertIn("Correct!", feedback)
        wrong, feedback = self.quiz.check_answer(question, (question.correct_answer + 1) % len(question.choices))
        self.assertFalse(wrong)
        self.assertIn("Incorrect.", feedback)

    def test_run_quiz(self):
        # Run without speech manager first to test silent mode
        score, questions = self.quiz.run_quiz(speech_manager=None, num_questions=1)
        self.assertEqual(questions, 1)
        self.assertEqual(score, 1)  # Should get perfect score in test mode
        
        # Run with speech manager, should not raise
        score, questions = self.quiz.run_quiz(self.speech, num_questions=1)
        self.assertEqual(questions, 1)
        self.assertEqual(score, 1)  # Should get perfect score in test mode

    def tearDown(self):
        self.speech.cleanup()

if __name__ == '__main__':
    unittest.main()
