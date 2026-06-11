import concurrent.futures

class NarrativeLLMClient:
    """
    Client wrapper for Google GenAI SDK calls to enforce the Graceful Degradation Guardrail.
    """

    FALLBACK_RESPONSE = "Deterministic score calculated successfully. AI narrative generation temporarily unavailable due to upstream latency."

    @staticmethod
    def generate_narrative(prompt: str, timeout_seconds: int = 5) -> str:
        """
        Wraps Google GenAI SDK calls in a strict timeout block and a generic Exception catch.
        If the LLM API fails, times out, or returns a flagged safety response, the system MUST NOT CRASH.
        Instead, it returns a static fallback string.
        """
        try:
            # Wrap the actual API call in a ThreadPoolExecutor to enforce a strict wall-clock timeout
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(NarrativeLLMClient._call_genai_sdk, prompt)
                # Enforce the strict timeout (e.g. 5 seconds)
                return future.result(timeout=timeout_seconds)
        except Exception:
            # Catches concurrent.futures.TimeoutError or any SDK-level exceptions (e.g. safety blocks, network errors)
            return NarrativeLLMClient.FALLBACK_RESPONSE

    @staticmethod
    def _call_genai_sdk(prompt: str) -> str:
        """
        Executes the actual google.genai SDK call.
        """
        # We import here to ensure the module doesn't crash on load if the SDK isn't installed yet
        import google.genai as genai
        
        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # If the response is blocked due to safety settings, text may be empty or raise an error
        if not response.text:
            raise ValueError("Response was flagged or empty.")
            
        return response.text
