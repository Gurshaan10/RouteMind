"""OpenAI client wrapper."""
from openai import OpenAI
from app.config import settings
from typing import Optional


class LLMClient:
    """Wrapper for OpenAI client with optional stub mode."""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.use_stub = False
        
        # Try to initialize the real OpenAI client if we have an API key.
        # If anything goes wrong (version mismatch, bad env, network issues),
        # we gracefully fall back to stub mode instead of crashing the API.
        api_key = settings.OPENAI_API_KEY
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as exc:  # pragma: no cover - defensive fallback
                print(
                    f"LLMClient: failed to initialize OpenAI client "
                    f"({exc!r}). Falling back to stub mode."
                )
                self.client = None
                self.use_stub = True
        else:
            self.use_stub = True
    
    def is_available(self) -> bool:
        """Check if real LLM is available."""
        return not self.use_stub
    
    async def generate_completion(
        self, system_prompt: str, user_prompt: str, model: Optional[str] = None
    ) -> str:
        """
        Generate text completion using OpenAI API or stub.
        
        Args:
            system_prompt: System message for the LLM
            user_prompt: User message/content
            model: Model name (defaults to config setting)
        
        Returns:
            Generated text response
        """
        if self.use_stub:
            return self._generate_stub_response(system_prompt, user_prompt)
        
        model_name = model or settings.OPENAI_MODEL
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            # Fallback to stub on error
            print(f"LLM API error: {e}. Using stub response.")
            return self._generate_stub_response(system_prompt, user_prompt)
    
    def _generate_stub_response(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Generate a stub response when LLM is not available."""
        return """This is a sample itinerary narrative. In production mode with an OpenAI API key configured, you would receive a personalized, detailed explanation of your travel itinerary here.

The narrative would include:
- A day-by-day overview of your planned activities
- Explanations for why specific activities were selected based on your preferences
- Tips for making the most of your trip
- Alternative suggestions if you want to modify your itinerary

To enable real LLM-generated narratives, set the OPENAI_API_KEY environment variable."""
