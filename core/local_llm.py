# core/local_llm.py
from llama_cpp import Llama 

class LocalLLM:
    def __init__(self, model_path, n_ctx=4096, n_threads=6, n_gpu_layers=40):
        self.model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )

    def generate(self, prompt, max_tokens=512, temperature=0.7):
        output = self.model(prompt, max_tokens=max_tokens, temperature=temperature)
        return output["choices"][0]["text"].strip()