from transformers import pipeline
import json

# Initialize chatbot (text-generation returns a list of dicts with 'generated_text')
chatbot = pipeline("text-generation", model="gpt2")

# Import safety quiz and speech manager
from safety_quiz import SafetyQuizManager
from speech_manager import SpeechManager, VoiceRole

safety_quiz = SafetyQuizManager()
speech_manager = SpeechManager()

# Simple assignment tracker
assignments = {}

def add_assignment(subject, task, due_date):
    assignments[subject] = {"task": task, "due_date": due_date}
    return f"Added {task} for {subject}, due {due_date}."

def list_assignments():
    if not assignments:
        return "No assignments yet."
    return "\n".join([f"{subject}: {info['task']} (Due: {info['due_date']})" for subject, info in assignments.items()])

def simple_quiz(topic):
    # Basic quiz logic (expand this later)
    if topic.lower() == "math":
        return "What's 2 + 2? Type your answer."
    elif topic.lower() == "history":
        return "Who was the first U.S. president? Type your answer."
    elif topic.lower() == "safety":
        return "What should you do first in case of a workplace emergency? (A) Run B) Assess the situation C) Call for help)"
    else:
        return "I can quiz you on Math, History, or Safety for now. Pick one!"

# Main chat loop
def chat_with_bot():
    welcome_msg = "Hi! I'm your schoolwork bot. Say 'add' to add an assignment, 'list' to see assignments, 'quiz' to study, or 'exit' to stop."
    print(welcome_msg)
    speech_manager.speak(welcome_msg, VoiceRole.GENERAL, play_sound=True)
    
    print("\nVoice commands available:")
    print("- 'voice listen': Enable voice recognition")
    print("- 'voice male/female': Change voice gender")
    print("- 'voice speed NUMBER': Adjust speaking rate")
    print("- 'voice volume NUMBER': Adjust volume")
    print("- 'voice language CODE': Change language (en, es, fr, de, it, ja)")
    print("- 'ambient start/stop': Control background sounds")
    
    # Start gentle background sound
    speech_manager.start_background_sound(0.05)
    
    voice_input_mode = False
    
    while True:
        if voice_input_mode:
            print("Listening for your command...")
            user_input = speech_manager.listen() or ""
            if not user_input:
                print("Sorry, I didn't catch that. Please try again.")
                continue
        else:
            user_input = input("You: ").lower()
        
        if user_input == "exit":
            goodbye_msg = "Goodbye! Have a great day!"
            print(goodbye_msg)
            speech_manager.speak(goodbye_msg, VoiceRole.SUCCESS, play_sound=True)
            speech_manager.cleanup()
            break
            
        elif user_input == "add":
            subject = input("Subject: ")
            task = input("Task: ")
            due_date = input("Due date: ")
            response = add_assignment(subject, task, due_date)
            print(response)
            speech_manager.speak(response)
            
        elif user_input == "list":
            response = list_assignments()
            print(response)
            speech_manager.speak(response)
            
        elif user_input == "quiz":
            topic = input("What topic to quiz? (Math, History, Safety): ").lower()
            if topic == "safety":
                print("Starting safety quiz. I'll read each question aloud.")
                speech_manager.speak("Starting safety quiz. I'll read each question aloud.")
                safety_quiz.run_quiz(speech_manager)
            else:
                response = simple_quiz(topic)
                print(response)
                speech_manager.speak(response)
                
        elif user_input.startswith("voice "):
            # Voice control commands
            cmd = user_input[6:]
            if cmd in ['male', 'female']:
                if speech_manager.change_voice(cmd):
                    response = f"Changed to {cmd} voice"
                else:
                    response = f"Sorry, no {cmd} voice available"
                print(response)
                speech_manager.speak(response)
            elif cmd.startswith('speed '):
                try:
                    speed = int(cmd.split()[1])
                    speech_manager.adjust_speech(rate=speed)
                    response = f"Speech speed adjusted to {speed}"
                    print(response)
                    speech_manager.speak(response)
                except:
                    print("Invalid speed command. Use 'voice speed NUMBER'")
            elif cmd.startswith('volume '):
                try:
                    vol = float(cmd.split()[1])
                    speech_manager.adjust_speech(volume=vol)
                    response = f"Volume adjusted to {vol}"
                    print(response)
                    speech_manager.speak(response)
                except:
                    print("Invalid volume command. Use 'voice volume NUMBER' (0.0-1.0)")
            elif cmd == 'listen':
                voice_input_mode = not voice_input_mode
                response = "Voice input mode " + ("enabled" if voice_input_mode else "disabled")
                print(response)
                speech_manager.speak(response, VoiceRole.SUCCESS, play_sound=True)
            elif cmd.startswith('language '):
                lang_code = cmd.split()[1].lower()
                if speech_manager.change_language(lang_code):
                    response = f"Language changed to {speech_manager.supported_languages[lang_code]}"
                else:
                    response = f"Unsupported language code. Use: {', '.join(speech_manager.supported_languages.keys())}"
                print(response)
                speech_manager.speak(response, VoiceRole.GENERAL)
        elif user_input.startswith('ambient '):
            cmd = user_input.split()[1].lower()
            if cmd == 'start':
                speech_manager.start_background_sound(0.05)
                response = "Background ambient sound started"
            elif cmd == 'stop':
                speech_manager.stop_background_sound()
                response = "Background ambient sound stopped"
            else:
                response = "Invalid ambient command. Use 'ambient start' or 'ambient stop'"
            print(response)
            speech_manager.speak(response)
        else:
            if user_input.startswith('mic test'):
                # optional: allow specifying device index e.g. 'mic test 0'
                parts = user_input.split()
                device = None
                if len(parts) > 2:
                    try:
                        device = int(parts[2])
                    except:
                        device = None
                result = speech_manager.record_and_recognize(duration=4, device_index=device)
                if result:
                    print(f"Recognized: {result}")
                    speech_manager.speak(f"I heard: {result}")
                else:
                    print("Could not recognize speech from mic test.")
                    speech_manager.speak("Could not recognize speech from mic test.")
                continue
            if user_input.startswith('mic set'):
                parts = user_input.split()
                if len(parts) < 3:
                    print("Usage: mic set <device_index> (or 'mic set none' to clear)")
                    continue
                if parts[2].lower() == 'none':
                    ok = speech_manager.set_default_mic(None)
                else:
                    try:
                        idx = int(parts[2])
                        ok = speech_manager.set_default_mic(idx)
                    except Exception:
                        ok = False
                print("Mic default set" if ok else "Failed to set mic default")
                continue
            # Use the chatbot model for general queries (text-generation)
            gen = chatbot(user_input, max_length=150, do_sample=True)
            # `gen` is a list of dicts like [{'generated_text': '...'}]
            bot_response = gen[0].get('generated_text', '')
            print(f"Bot: {bot_response}")
            speech_manager.speak(bot_response)

if __name__ == "__main__":
    chat_with_bot()