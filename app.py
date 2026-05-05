from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# ========================
# API Key - Hugging Face Secrets se aayegi
# HF Space Settings > Secrets > OPENROUTER_API_KEY
# ========================
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model to use
MODEL = "meta-llama/llama-3.3-70b-instruct"


def generate_architecture_design(prompt: str, style: str, use_case: str) -> dict:
    system_prompt = """You are an expert AI Architecture Designer. When given a prompt about any object, system, or concept, you generate a detailed, professional architectural design document.

Your response MUST follow this exact structure with these section headers:

## 🏗️ Architecture Overview
Brief description of the overall architectural approach.

## 📐 Core Components
List and describe the main components/modules with their roles.

## 🔄 Data Flow & Interactions
Explain how components interact and data moves through the system.

## 🧱 Layer Architecture
Describe the layered structure (e.g., Presentation, Business Logic, Data layers).

## ⚙️ Technology Stack
Recommended technologies, frameworks, and tools for each component.

## 🔗 Integration Points
APIs, external services, or interfaces the system connects with.

## 🛡️ Security & Scalability
Security considerations and how the system scales.

## 📊 ASCII Architecture Diagram
Provide a clear ASCII art diagram showing the architecture layout.

## ✅ Key Design Principles
List the core principles guiding this architecture.

Be detailed, technical, and professional. Format everything in clean Markdown."""

    user_message = f"""Design a complete architecture for: **{prompt}**

Design Style: {style}
Use Case / Context: {use_case}

Generate a comprehensive, production-ready architecture design document."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://huggingface.co/spaces",
        "X-Title": "AI Architecture Design Generator"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 3000,
        "temperature": 0.7
    }

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        raise Exception(f"OpenRouter API Error {response.status_code}: {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    return {
        "design": content,
        "model": data.get("model", MODEL),
        "tokens_used": data.get("usage", {}).get("total_tokens", "N/A")
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if not OPENROUTER_API_KEY:
        return jsonify({
            "error": "API key not set. Please add OPENROUTER_API_KEY in Hugging Face Space Secrets."
        }), 500

    try:
        body = request.get_json()
        prompt = body.get("prompt", "").strip()
        style = body.get("style", "Modern & Scalable")
        use_case = body.get("use_case", "General Purpose")

        if not prompt:
            return jsonify({"error": "Please provide a prompt describing what to design."}), 400

        result = generate_architecture_design(prompt, style, use_case)

        return jsonify({
            "success": True,
            "design": result["design"],
            "model": result["model"],
            "tokens_used": result["tokens_used"],
            "prompt": prompt
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to OpenRouter API. Check your internet connection."}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({
        "status": "running",
        "model": MODEL,
        "api_key_set": bool(OPENROUTER_API_KEY)
    })


if __name__ == "__main__":
    # Hugging Face ke liye port 7860 aur host 0.0.0.0
    app.run(host="0.0.0.0", port=7860, debug=False)
 
