from huggingface_hub import InferenceClient
client = InferenceClient()  # automatically uses HF Inference Providers free tier

output = client.text_generation(
    "Write a poem about technology",
    model="meta-llama/Meta-Llama-3-8B-Instruct"
)
print(output)