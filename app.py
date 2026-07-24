import gradio as gr
import os

with gr.Blocks(title="Retail-Heros", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏪 Retail-Heros - Version Stable")
    gr.Markdown("L'application est en ligne et fonctionne correctement.")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🔐 Authentification")
            gr.Markdown("Connectez-vous avec `admin` / `admin123`")
        with gr.Column():
            gr.Markdown("### 📸 Analyse d'images")
            gr.Markdown("Bientôt disponible avec YOLO")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        root_path="/"
    )
