from huggingface_hub import InferenceClient

from .config import HF_MODEL, HF_TOKEN
from .lang import detect_language

SYSTEM_PROMPTS = {
    "ar": """أنت مستشار ShopSpace للأعمال في الإسكندرية.
أجب بالعربية الواضحة وبالاعتماد فقط على المراجع المقدمة لك.
إذا لم تكن المراجع كافية، قل بوضوح إن المعلومات المتاحة لا تكفي ولا تخمّن.
لا تقدّم استشارة قانونية أو مالية مهنية، واذكر التنبيه عند الحديث عن التراخيص أو العقود.
كن عمليًا ومختصرًا، وقدّم توصيات قابلة للتنفيذ.""",
    "en": """You are the ShopSpace business advisor for Alexandria.
Answer clearly in English, relying only on the reference material provided to you.
If the references aren't enough, say plainly that the available information isn't sufficient -- don't guess.
Don't give legal or financial professional advice, and mention the disclaimer when discussing licenses or contracts.
Be practical and concise, and give actionable recommendations.""",
}

USER_TEMPLATES = {
    "ar": "المراجع المتاحة:\n{context}\n\nسؤال المستخدم: {question}",
    "en": "Available references:\n{context}\n\nUser question: {question}",
}


def answer(question: str, context: str) -> str:
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is not configured. Add it to the .env file or Hugging Face Space secrets.")

    language = detect_language(question)
    system_prompt = SYSTEM_PROMPTS[language]
    user_content = USER_TEMPLATES[language].format(context=context, question=question)

    client = InferenceClient(provider="featherless-ai", token=HF_TOKEN)
    response = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=700,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
