import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from chatbot.memory import JSONChatMemory
from chatbot.openrouter import OpenRouterAPIError, OpenRouterClient, OpenRouterConfigurationError
from chatbot.speech import VoiceRecognitionError, VoiceTranscriber


@login_required
def chat_page(request):
    memory = JSONChatMemory.from_settings()
    journal = memory.clear_history(request.user)
    return render(request, "chatbot/chat.html", {"chat_history": journal["history"][-20:]})


@login_required
@require_POST
def chat_message(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    question = (payload.get("message") or "").strip()
    source = (payload.get("source") or "text").strip()[:32]
    if not question:
        return JsonResponse({"error": "Message is required."}, status=400)

    memory = JSONChatMemory.from_settings()
    turn_id = memory.record_user_question(
        user=request.user,
        question=question,
        metadata={"source": source},
    )

    messages = memory.history_as_messages(user=request.user, limit=16)

    try:
        result = OpenRouterClient().chat(messages=messages, user_id=request.user.id)
    except (OpenRouterConfigurationError, OpenRouterAPIError) as exc:
        memory.record_assistant_answer(
            user=request.user,
            turn_id=turn_id,
            answer="Сейчас не удалось получить ответ от AI-сервиса. Попробуйте еще раз позже.",
            metadata={"error": str(exc)},
        )
        return JsonResponse({"error": str(exc)}, status=502)

    memory.record_assistant_answer(
        user=request.user,
        turn_id=turn_id,
        answer=result.content,
        metadata={
            "model": result.model,
            "response_id": result.response_id,
            "usage": result.usage,
        },
    )
    return JsonResponse(
        {
            "answer": result.content,
            "turn_id": turn_id,
            "model": result.model,
            "usage": result.usage,
        }
    )


@login_required
@require_POST
def transcribe_audio(request):
    uploaded_audio = request.FILES.get("audio")
    if not uploaded_audio:
        return JsonResponse({"error": "Audio file is required."}, status=400)

    language = request.POST.get("language") or "ru-RU"
    try:
        transcript = VoiceTranscriber(language=language).transcribe_upload(uploaded_audio)
    except VoiceRecognitionError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"transcript": transcript})
