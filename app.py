import gradio as gr
import os

# Interface simple
def greet(name):
    return f"Bonjour {name} !"

iface = gr.Interface(
    fn=greet,
    inputs=gr.Textbox(label="Votre nom"),
    outputs=gr.Textbox(label="Message"),
    title="🏪 Retail-Heros - Test",
    description="L'application est en ligne !"
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    iface.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        root_path="/"
    )
