from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Carregar modelo e tokenizer
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

def generate_text(prompt, max_length=100):
    input_ids = tokenizer.encode(prompt, return_tensors='pt')
    output = model.generate(input_ids, max_length=max_length, num_return_sequences=1, no_repeat_ngram_size=2, early_stopping=True)
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return generated_text

# Exemplo de uso
prompt = "A machine learning model that"
generated_text = generate_text(prompt)
print("Texto gerado:")
print(generated_text)
