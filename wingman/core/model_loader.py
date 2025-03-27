from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from openai import OpenAI

class ModelLoader():
    '''
    Loads selected model into the Wingman
    '''
    def __init__(self, model, apiKey):
        self.model = model
        self.apiKey = apiKey

    def load_model(self):
        models = {'mistral-saba-24b': ChatGroq,'llama3.2': ChatOllama, 'qwen-2.5-32b':ChatGroq, 'llama-3.3-70b-versatile':ChatGroq, 'gpt-3.5':ChatOpenAI, 'gpt4':ChatOpenAI, 'claude3.5-sonnet':ChatAnthropic}
        model_class = models.get(self.model)

        if model_class is None:
            raise ValueError(f'{self.model} is not a valid model.') 

        if self.model == 'llama3.2':
            return model_class(model=self.model, temperature=0.7)

        return model_class(model=self.model, api_key=self.apiKey, temperature=0.6)
    
    def load_client(self):
        return OpenAI(
            base_url="https://api.groq.com/openai/v1",
            # base_url="http://localhost:11434/v1",
            api_key=self.apiKey
        )
        
