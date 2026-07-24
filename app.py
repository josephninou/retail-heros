import gradio as gr
import os

def greet(name):
    return "Bonjour " + name + " !"

with gr.Blocks() as demo:
    gr.Markdown("# 🏪 Test Retail-Heros")
    name = gr.Textbox(label="Nom")
    btn = gr.Button("Dire bonjour")
    output = gr.Textbox(label="Réponse")
    btn.click(fn=greet, inputs=name, outputs=output)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    demo.launch(server_name="0.0.0.0", server_port=port)
