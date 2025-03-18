import os
import time
import gradio as gr
from groq import Groq
from dotenv import load_dotenv
from better_profanity import profanity
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes

# Load environment variables and initialize Groq client
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "gemma2-9b-it"

# Load the default list of profane words
profanity.load_censor_words()

system_prompt = """You are a compassionate mental health supporter dedicated exclusively to mental health and wellbeing issues. 
Respond with empathy, understanding, and concise advice. Focus on providing helpful, actionable tips that are easy for the user to process. 
If the query is not directly related to mental health, gently remind the user that your expertise is in this area and encourage them to ask a relevant question. 
Always suggest seeking professional help when appropriate, and offer brief suggestions without overwhelming the user with too much information at once."""

def safe_message_processing(message):
    """
    Checks the input message for profanity and crisis/self-harm indicators.
    Returns a safe response if an issue is detected; otherwise, returns the original message.
    """
    # check for profanity
    if profanity.contains_profanity(message):
        return "Your message contains inappropriate language. Could you please rephrase your question?"

    # check for self-harm or crisis-related keywords
    crisis_keywords = ["suicide", "kill myself", "self harm", "end my life", "hopeless", "worthless", "despair"]
    if any(word in message.lower() for word in crisis_keywords):
        return ("I'm really sorry that you're feeling this way. It sounds like you're in distress. "
                "If you're in immediate danger or feel unsafe, please consider calling your local emergency services immediately. "
                "It might also help to reach out to someone you trust or a mental health professional.")
        
    # if no issues are found, return the original message
    return message

def format_message(role, content):
    return {"role": role, "content": content}

def respond(message, mood, history, lang):
    # run safety checks on the user's message
    safe_message = safe_message_processing(message)
    if safe_message != message:
        # if a safety check triggered, append the safe response and skip further processing
        history.append(format_message("assistant", safe_message))
        return history, ""
    try:
        # choose the system prompt based on language selection
        if lang == "Français":
            system_prompt_lang = (
                "Vous êtes un soutien attentionné en santé mentale, dédié exclusivement aux questions de santé mentale "
                "et de bien-être. Répondez avec empathie et compréhension, en fournissant des informations complètes et approfondies "
                "pour soutenir les questions de l'utilisateur. Si une question n'est pas liée à la santé mentale, rappelez doucement à l'utilisateur "
                "que votre expertise est limitée au soutien en santé mentale et encouragez-le à poser une question pertinente. "
                "Suggérez toujours de consulter un professionnel lorsque cela est approprié."
            )
        else:
            system_prompt_lang = system_prompt

        # build the conversation history including the system prompt and current mood
        messages = [
            format_message("system", f"{system_prompt_lang}\nCurrent mood: {mood}"),
            *history,
            format_message("user", message)
        ]
        clean_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages if "role" in msg and "content" in msg
        ]
        completion = client.chat.completions.create(
            model=MODEL,
            messages=clean_messages,
            temperature=0.7,
            max_tokens=512,
            top_p=1
        )
        reply = completion.choices[0].message.content
        history.append(format_message("user", message))
        history.append(format_message("assistant", reply))

        return history, ""

    except Exception as e:
        return history, f"Error: {str(e)}"

def update_send_button(message):
    return gr.update(interactive=bool(message))

def new_chat():
    return [], ""

def update_ui_text(selected_lang):
    if selected_lang == "Français":
        header_text = "<h1 id='equilibria-heading'>🌱 Équilibre</h1>"
        subheader_text = "<h2>Votre compagnon de santé mentale. Comment puis-je vous aider aujourd'hui?</h2>"
        placeholder = "Tapez votre message..."
        mood_choices = ["Calme 😌", "Triste 😢", "Anxieux 😰", "Neutre 😐", "Je ne suis pas sûr..."]
        default_mood = "Neutre 😐"
        mood_label = "Comment vous sentez-vous ?"
        send_button_text = "Envoyer"
        new_chat_button_text = "Nouvelle discussion"

        prompt1_text = "Partagez un conseil positif sur la santé mentale"
        prompt2_text = "Comment gérer l'anxiété ?"
        prompt3_text = "J'ai besoin d'encouragement"
        prompt4_text = "Quel est un exercice rapide de soulagement du stress ?"
    else:
        header_text = "<h1 id='equilibria-heading'>🌱 Equilibria</h1>"
        subheader_text = "<h2>Your personal mental health companion. How can I support you today?</h2>"
        placeholder = "Type your message..."
        mood_choices = ["Calm 😌", "Sad 😢", "Anxious 😰", "Neutral 😐", "I'm not sure..."]
        default_mood = "Neutral 😐"
        mood_label = "How are you feeling?"
        send_button_text = "Send"
        new_chat_button_text = "New Chat"

        prompt1_text = "Share a positive mental health tip"
        prompt2_text = "How can I manage anxiety?"
        prompt3_text = "I need some encouragement"
        prompt4_text = "What's a quick stress relief exercise?"

    return (
        gr.update(value=header_text),
        gr.update(value=subheader_text),
        gr.update(placeholder=placeholder),
        gr.update(choices=mood_choices, value=default_mood, label=mood_label),
        gr.update(value=prompt1_text),
        gr.update(value=prompt2_text),
        gr.update(value=prompt3_text),
        gr.update(value=prompt4_text),
        gr.update(value=send_button_text, elem_id="send-btn"),
        gr.update(value=new_chat_button_text, elem_id="new-chat")
    )

def get_prompt_text(prompt_id, lang):
    prompts = {
        "English": {
            "prompt1": "Share a positive mental health tip",
            "prompt2": "How can I manage anxiety?",
            "prompt3": "I need some encouragement",
            "prompt4": "What's a quick stress relief exercise?"
        },
        "Français": {
            "prompt1": "Partagez un conseil positif sur la santé mentale",
            "prompt2": "Comment gérer l'anxiété ?",
            "prompt3": "J'ai besoin d'encouragement",
            "prompt4": "Quel est un exercice rapide de soulagement du stress ?"
        }
    }
    return prompts.get(lang, prompts["English"]).get(prompt_id, "")

def inject_fonts():
    return """
    <script>
        let fontLink = document.createElement("link");
        fontLink.href = "https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Great+Vibes&family=Nunito:wght@300;400;600&display=swap";
        fontLink.rel = "stylesheet";
        document.head.appendChild(fontLink);
    </script>
    """

# Additional custom CSS (kept minimal to support the theme)
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Great+Vibes&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600&display=swap');

:root {
    --primary: #4CAF50 !important;
}

#equilibria-heading {
    color: #4CAF4F !important;
}

.gradio-container-5-20-0 .prose h1 {
    font-family: 'Cinzel', serif !important;
    font-size: 42px !important;
    font-weight: 700 !important;
    text-align: center !important;
    color: var(--primary) !important;
    letter-spacing: 1.5px !important;
    margin-bottom: 10px !important;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1) !important;
}

textarea {
    min-height: 70px !important;
    font-size: 16px !important;
    padding: 10px !important;
}

#chatbox {
    font-family: 'Nunito', sans-serif !important;
    font-size: 16px !important;
}

.gradio-container-5-20-0 {
    font-family: 'Nunito', sans-serif !important;
}

.gradio-container-5-20-0 .prose h2 {
    font-family: 'Nunito', sans-serif !important;
    font-size: 20px !important;
    text-align: center !important;
    color: #666 !important;
}

.block.svelte-11xb1hd {
    overflow: hidden !important;
    min-width: 100% !important;
}
"""

# custom theme
class CustomTheme(Base):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.green,
        secondary_hue: colors.Color | str = colors.neutral,
        neutral_hue: colors.Color | str = colors.gray,
        spacing_size: sizes.Size | str = sizes.spacing_sm,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_md,
        font: fonts.Font | str | list = (
            fonts.GoogleFont("Nunito"),
            "sans-serif",
        ),
        font_mono: fonts.Font | str | list = (
            fonts.GoogleFont("IBM Plex Mono"),
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )

        super().set(
            body_background_fill="#F7F9FC",
            button_primary_background_fill="*primary_300",
            button_primary_background_fill_hover="*primary_400",
            button_primary_text_color="*neutral_900",
            block_border_width="0px",
            block_shadow="none",
            slider_color="*primary_500",
            block_title_text_color="#4CAF4F"
        )

# instantiate custom theme
custom_theme = CustomTheme()

with gr.Blocks(css=custom_css, theme=custom_theme) as app:
    gr.HTML(inject_fonts())
    
    # header texts
    header = gr.Markdown("<h1 id='equilibria-heading'>🌱 Equilibria</h1>")
    subheader = gr.Markdown("<h2>Your personal mental health companion. How can I support you today?</h2>")
    
    with gr.Row():
        with gr.Column(scale=2):
            mood = gr.Dropdown(
                choices=["Calm 😌", "Sad 😢", "Anxious 😰", "Neutral 😐", "I'm not sure..."],
                label="How are you feeling?",
                value="Neutral 😐",
                interactive=True,
                elem_id="mood-selector",
                multiselect=False,
                allow_custom_value=False
            )
        with gr.Column(scale=1):
            language = gr.Radio(
                ["English", "Français"],
                label="Language / Langue",
                value="English",
                interactive=True
            )
    
    chatbot = gr.Chatbot(
        type="messages", 
        height=500, 
        elem_id="chatbox",
        show_label=False
    )
    
    # prompt buttons
    with gr.Row(equal_height=True):
        prompt1 = gr.Button(value="Share a positive mental health tip", elem_classes="prompt-btn")
        prompt2 = gr.Button(value="How can I manage anxiety?", elem_classes="prompt-btn")
        prompt3 = gr.Button(value="I need some encouragement", elem_classes="prompt-btn")
        prompt4 = gr.Button(value="What's a quick stress relief exercise?", elem_classes="prompt-btn")
    
    # message input textbox and Send button
    msg = gr.Textbox(
        placeholder="Type your message...",
        lines=1,
        elem_id="input-msg",
        interactive=True,
        show_label=False
    )
    
    btn = gr.Button(
        "Send",
        elem_id="send-btn",
        variant="primary",
        interactive=False
    )

    new_chat_btn = gr.Button("New Chat", elem_id="new-chat")
    
    # register prompt button clicks
    prompt1.click(lambda lang: get_prompt_text("prompt1", lang), inputs=language, outputs=msg)
    prompt2.click(lambda lang: get_prompt_text("prompt2", lang), inputs=language, outputs=msg)
    prompt3.click(lambda lang: get_prompt_text("prompt3", lang), inputs=language, outputs=msg)
    prompt4.click(lambda lang: get_prompt_text("prompt4", lang), inputs=language, outputs=msg)
    
    # language change callback
    language.change(update_ui_text, language, [header, subheader, msg, mood, prompt1, prompt2, prompt3, prompt4, btn, new_chat_btn])
    
    msg.change(update_send_button, [msg], [btn])
    btn.click(respond, [msg, mood, chatbot, language], [chatbot, msg])
    msg.submit(respond, [msg, mood, chatbot, language], [chatbot, msg])
    
    with gr.Row():
        new_chat_btn.click(fn=new_chat, inputs=None, outputs=[chatbot, msg])

    # disclaimer
    gr.Markdown("""
    <div style="text-align: center; color: #666; margin-top: 20px;">
    <small>Note: This is an AI companion, not a substitute for professional care.</small>
    </div>
    """)

if __name__ == "__main__":
    app.launch()
