from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from services import AIService

support_bp = Blueprint('support', __name__)


@support_bp.route('/help')
@login_required
def help_page():
    return render_template('help_chat.html')


@support_bp.route('/api/help/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get('message', '')).strip()
    if not message:
        return jsonify(error='Enter a question to start the chat.'), 400
    if len(message) > 2000:
        return jsonify(error='Please keep your question under 2,000 characters.'), 400

    history = data.get('history', [])
    if not isinstance(history, list):
        history = []
    safe_history = []
    for item in history[-10:]:
        if not isinstance(item, dict) or item.get('role') not in ('user', 'assistant'):
            continue
        content = str(item.get('content', '')).strip()[:1200]
        if content:
            safe_history.append({'role': item['role'], 'content': content})

    answer = AIService.chat_support(message, safe_history, current_user.role)
    if not answer:
        return jsonify(error=(
            'The Groq AI service did not respond. Check that your GROQ_API_KEY is configured '
            f'and that model "{current_app.config.get("GROQ_MODEL", "openai/gpt-oss-120b")}" is active.'
        )), 503
    return jsonify(answer=answer)
