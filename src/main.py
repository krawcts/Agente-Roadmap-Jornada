from huggingface_hub import InferenceClient

from dotenv import load_dotenv
import os

load_dotenv()
HF_TOKEN = os.getenv('HF_TOKEN')

client = InferenceClient(
    "meta-llama/Llama-3.2-3B-Instruct",
    token=f"{HF_TOKEN}",
)


prompt="""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

The capital of france is<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

output = client.text_generation(
    prompt,
    max_new_tokens=100,
)

print(output)