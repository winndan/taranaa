from fasthtml.common import *
from monsterui.all import *
from agents.master_agent import route_query
import re

def mk_inp():
    return Input(
        id='msg',
        placeholder="Ask me anything about your trip...",
        autofocus=True,
        cls="w-full"
    )

def _format_response(response):
    """Convert markdown formatting to FastHTML components"""
    if not isinstance(response, str):
        return response

    emoji_map = [
        ("hotel", "🏨"),
        ("flight", "✈️"),
        ("restaurant", "🍽️"),
        ("budget", "💰"),
        ("recommend", "🌟"),
        ("weather", "☀️"),
        ("important", "❗"),
        ("tip", "💡"),
        ("beach", "🏖️"),
        ("mountain", "⛰️"),
        ("city", "🏙️"),
        ("museum", "🏛️"),
        ("food", "🍜"),
        ("shopping", "🛍️")
    ]

    # Emoji replacement
    for word, emoji in emoji_map:
        response = response.replace(f" {word} ", f" {emoji} ")
        response = response.replace(f" {word.capitalize()} ", f" {emoji} ")
        response = response.replace(f"{word}-", f"{emoji}-")

    # Create components for each line
    lines = []
    for line in response.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Handle bold sections
        bold_sections = re.findall(r'\*\*(.*?)\*\*', line)
        if bold_sections:
            parts = []
            remaining = line
            for section in bold_sections:
                before, sep, remaining = remaining.partition(f"**{section}**")
                if before:
                    parts.append(before)
                parts.append(Span(section, cls="title-bold"))
            if remaining:
                parts.append(remaining)
            if remaining:
                parts.append(remaining)
            lines.append(Div(*parts, cls="mb-1"))
        elif line.startswith("- "):
            lines.append(Div(Span(line[2:], cls="list-item"), cls="ml-4"))
        else:
            lines.append(Div(line, cls="mb-1"))

    return lines

def _chat_ui(sender, msg):
    is_user = sender == "User"
    name = "Traveler" if is_user else "Bot"
    avatar = DiceBearAvatar(name, 10, 10)

    bubble_cls = "bg-blue-100 text-blue-900" if is_user else "bg-gray-100 text-gray-800"
    alignment_cls = "flex-row-reverse text-right" if is_user else "flex-row text-left"

    # Handle both string and component messages
    message_content = msg if isinstance(msg, str) else Div(*msg) if isinstance(msg, list) else msg

    return Div(
        Div(
            avatar,
            Div(
                Span(sender, cls="text-xs text-gray-500 mb-1"),
                Div(
                    message_content,
                    cls=f"{bubble_cls} p-3 rounded-xl max-w-sm w-fit break-words"
                ),
                cls="flex flex-col space-y-1"
            ),
            cls=f"flex items-start gap-3 {alignment_cls}"
        ),
        cls="w-full"
    )

async def chatchat(request):
    cts = Container(
        Card(
            DivCentered(H2("Travel Chatbot 🤖"), cls="mb-4"),
            Div(
                id='notifications',
                cls="flex flex-col space-y-2 max-h-96 overflow-y-auto p-4 bg-white rounded-lg border border-gray-200"
            ),
            Div(
                Form(
                    mk_inp(),
                    Button("Send", cls=ButtonT.primary, type="submit", id="send_button", ws_send=True),
                    id='form',
                    cls="flex gap-2 items-center",
                    ws_send=True
                ),
                cls="pt-3"
            ),
            cls="p-6 max-w-xl mx-auto shadow-lg rounded-2xl bg-white"
        ),
        hx_ext='ws',
        ws_connect='/ws'
    )
    return cts

async def on_connect(send):
    print('Connected!')
    await send(_chat_ui("Bot", "Hello! ✨ Where shall we explore today?"))

async def on_disconnect(ws):
    print('Disconnected!')

async def ws(msg: str, send):
    user_msg = _chat_ui("User", msg)

    loading_bubble = Div(
        Div(
            DiceBearAvatar("Bot", 10, 10),
            Div(
                Span("Bot", cls="text-xs text-gray-500 mb-1"),
                Div(Loading(), cls="bg-gray-100 p-3 rounded-xl shadow max-w-sm w-fit"),
                cls="flex flex-col"
            ),
            cls="flex items-start gap-3"
        ),
        id="bot-loading",
        cls="w-full"
    )

    await send(loading_bubble)
    #await sleep(0.1)

    bot_response = await route_query(msg)
    bot_text = bot_response.output if hasattr(bot_response, "output") else bot_response
    formatted_lines = _format_response(bot_text)
    
    bot_msg = Div(
        Div(
            DiceBearAvatar("Bot", 10, 10),
            Div(
                Span("Bot", cls="text-xs text-gray-500 mb-1"),
                Div(
                    *formatted_lines,
                    cls="bg-gray-100 p-3 rounded-xl max-w-sm w-fit break-words"
                ),
                cls="flex flex-col space-y-1"
            ),
            cls="flex items-start gap-3"
        ),
        cls="w-full"
    )

    await send(Div(user_msg, bot_msg, id="notifications"))
    return mk_inp()
