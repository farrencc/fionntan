import google.generativeai as genai
genai.configure(api_key='AIzaSyDNY2saiOj2KMQKakXVXYUeVGSPpcNxt1U"')

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(model.name)
