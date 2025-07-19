from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = 'google-t5/t5-small'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

tokenizer.save_pretrained('flashlog/models/t5-small')
model.save_pretrained('flashlog/models/t5-small')
print('Model downloaded to flashlog/models/t5-small')