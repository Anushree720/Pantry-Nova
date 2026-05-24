import json
import uuid
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from accounts.decorators import household_member_required
from .models import ChatMessage


SYSTEM_PROMPT = (
    "You are Nova, Pantry Nova's AI sustainability assistant. Help users with: "
    "food storage tips and best practices, recipes using expiring ingredients, "
    "waste reduction strategies, grocery shopping advice, nutritional information, "
    "and platform usage. When a user asks about expiring items, suggest creative recipes. "
    "Always encourage sustainable food habits. Be friendly, practical, and eco-conscious. "
    "Keep responses concise and actionable."
)


def _expiring_items_context(user):
    try:
        if user.user_type == 'manager':
            h = user.kitchenmanager.household
        elif user.user_type == 'member':
            h = user.familymember.household
        else:
            return ''
    except Exception:
        return ''
    from inventory.models import PantryItem
    today = date.today()
    week_end = today + timedelta(days=7)
    items = PantryItem.objects.filter(
        household=h, is_consumed=False, expiry_date__lte=week_end
    ).order_by('expiry_date')[:5]
    if not items:
        return ''
    lines = ['User has these expiring items:']
    for item in items:
        days = (item.expiry_date - today).days
        lines.append(f'- {item.item_name} ({item.quantity}{item.unit}) — {days} days left')
    return '\n'.join(lines)


def _gemini_response(user_message, user, session_id):
    """Call Gemini API or fallback."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return _fallback_response(user_message)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        context = _expiring_items_context(user)
        sys_prompt = SYSTEM_PROMPT
        if context:
            sys_prompt += '\n\n' + context

        history_msgs = ChatMessage.objects.filter(
            user=user, session_id=session_id
        ).order_by('-timestamp')[:10]
        history = []
        for msg in reversed(list(history_msgs)):
            history.append({'role': 'user', 'parts': [msg.message]})
            history.append({'role': 'model', 'parts': [msg.response]})

        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=sys_prompt,
        )
        chat = model.start_chat(history=history)
        resp = chat.send_message(user_message)
        return resp.text
    except Exception as e:
        return _fallback_response(user_message) + f"\n\n_(AI temporarily unavailable)_"


def _fallback_response(message):
    """Simple keyword-based fallback when Gemini API is unavailable."""
    msg = message.lower()
    if any(w in msg for w in ['recipe', 'cook', 'make', 'prepare']):
        return ("🌿 Try a quick stir-fry! Sauté your expiring vegetables with garlic, "
                "olive oil, and a splash of soy sauce. Serve over rice or noodles. "
                "Stir-fries are the perfect way to use up produce before it spoils.")
    if any(w in msg for w in ['storage', 'store', 'preserve', 'fridge']):
        return ("🌿 Storage tips:\n• Leafy greens: airtight container with paper towel\n"
                "• Tomatoes: counter, not fridge\n• Herbs: trim stems, place in water\n"
                "• Bread: freezer for long-term storage\n• Onions/garlic: cool, dry, dark place")
    if any(w in msg for w in ['waste', 'reduce', 'save']):
        return ("♻️ Top waste-reduction tips:\n• Plan meals weekly\n• Shop with a list\n"
                "• Use 'First In, First Out' rule\n• Freeze surplus produce\n"
                "• Compost food scraps\n• Track your inventory in Pantry Nova!")
    if any(w in msg for w in ['shopping', 'grocery', 'buy']):
        return ("🛒 Smart shopping:\n• Check Pantry Nova inventory first\n"
                "• Make a list and stick to it\n• Don't shop hungry\n"
                "• Buy seasonal produce\n• Choose frozen for items you use rarely")
    if any(w in msg for w in ['hello', 'hi', 'hey']):
        return ("🌿 Hi! I'm Nova, your Pantry Nova AI assistant. I can help with recipes, "
                "storage tips, waste reduction, and shopping advice. What's cooking today?")
    return ("🌿 I'm here to help with food storage, recipes, waste reduction, and shopping advice. "
            "Try asking: 'What can I make with expiring items?' or 'How do I store fresh herbs?'")


@household_member_required
def chatbot(request):
    user = request.current_user
    session_id = request.session.get('chat_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())[:12]
        request.session['chat_session_id'] = session_id

    history = ChatMessage.objects.filter(
        user=user, session_id=session_id
    ).order_by('timestamp')

    sessions = ChatMessage.objects.filter(user=user).values('session_id').distinct()[:10]

    return render(request, 'chatbot/chatbot.html', {
        'page_title': 'Nova AI Assistant',
        'history': history,
        'session_id': session_id,
        'sessions': sessions,
    })


@household_member_required
@csrf_exempt
def chatbot_send(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST
    message = (data.get('message') or '').strip()
    if not message:
        return JsonResponse({'success': False, 'error': 'Empty message'})

    session_id = request.session.get('chat_session_id', 'default')
    response = _gemini_response(message, request.current_user, session_id)

    ChatMessage.objects.create(
        user=request.current_user,
        message=message,
        response=response,
        session_id=session_id,
    )
    return JsonResponse({'success': True, 'response': response})


@household_member_required
def chatbot_new(request):
    request.session['chat_session_id'] = str(uuid.uuid4())[:12]
    return redirect('chatbot')


@household_member_required
def chatbot_history(request):
    user = request.current_user
    sessions = ChatMessage.objects.filter(user=user).order_by('-timestamp')[:50]
    return render(request, 'chatbot/history.html', {
        'page_title': 'Chat History',
        'sessions': sessions,
    })
