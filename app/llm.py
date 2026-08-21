from huggingface_hub import InferenceClient
import logging

from .config import HF_MODEL, HF_TOKEN

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """أنت مستشار ShopSpace للأعمال في الإسكندرية.
أجب بشكل مختصر وواضح في 3-5 جمل فقط بالاعتماد على المراجع المقدمة لك.
إذا لم تكن المراجع كافية، قل بوضوح إن المعلومات لا تكفي ولا تخمّن.
لا تقدّم استشارة قانونية أو مالية مهنية. كن عمليًا وتجنب التكرار والنقاط المرقمة."""


def answer(question: str, context: str) -> str:
    if not HF_TOKEN:
        error_msg = "HF_TOKEN is not configured. Add it to the .env file or Hugging Face Space secrets."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Calling Qwen LLM for response generation")
    client = InferenceClient(provider="featherless-ai", token=HF_TOKEN)
    try:
        response = client.chat.completions.create(
            model=HF_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"المراجع المتاحة:\n{context}\n\nسؤال المستخدم: {question}",
                },
            ],
            max_tokens=300,
            temperature=0.2,
        )
        logger.debug("Response generated successfully from LLM")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM error: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to generate response: {str(e)}") from e
