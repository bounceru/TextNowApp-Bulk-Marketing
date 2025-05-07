"""
Utility script to generate sample voicemail greetings
using text-to-speech for the ProgressGhostCreator demo
"""
import os
import pyttsx3
import random

def generate_sample_voicemails(count=10, output_dir="voicemail"):
    """Generate sample voicemail greetings using text-to-speech"""
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample greeting templates
    greeting_templates = [
        "Hi, you've reached {name}. I can't come to the phone right now. Please leave a message after the tone.",
        "Hello, this is {name}. Sorry I missed your call. Please leave a message and I'll get back to you as soon as possible.",
        "You've reached {name}'s voicemail. Please leave your name, number, and a brief message, and I'll return your call.",
        "Hi there, {name} speaking. I'm not available right now. Leave a message and I'll call you back.",
        "Thanks for calling {name}. I'm unavailable at the moment. Please leave a detailed message after the beep.",
        "Hello, you've reached {name}. I'm either away from my phone or busy. Leave a message and I'll call you back soon.",
        "This is {name}. Sorry I couldn't answer. Leave a message and I'll get back to you.",
        "Hi, this is {name}'s phone. I'm not available right now, but if you leave a message, I'll return your call as soon as I can.",
        "You've reached {name}. I'm unable to take your call right now. Please leave your contact information, and I'll get back to you.",
        "Hello, {name} here. I'm currently unavailable. Please leave your name and number, and I'll call you back soon."
    ]
    
    # Sample names
    names = [
        "John", "Emily", "Michael", "Jessica", "David", "Sarah", "Robert", "Jennifer", 
        "James", "Lisa", "William", "Mary", "Richard", "Patricia", "Charles", "Linda", 
        "Daniel", "Elizabeth", "Matthew", "Barbara"
    ]
    
    # Initialize text-to-speech engine
    engine = pyttsx3.init()
    
    # Generate sample voicemails
    for i in range(count):
        # Choose a random name and greeting template
        name = random.choice(names)
        template = random.choice(greeting_templates)
        greeting = template.format(name=name)
        
        # Set a unique filename
        filename = f"voicemail_{i+1:02d}_{name.lower()}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # Generate and save the voicemail
        print(f"Generating voicemail {i+1}/{count}: {greeting}")
        
        # Save to file
        engine.save_to_file(greeting, filepath)
        engine.runAndWait()
        
        print(f"Saved to {filepath}")
    
    print(f"Generated {count} sample voicemail greetings in {output_dir}")

if __name__ == "__main__":
    generate_sample_voicemails(10)