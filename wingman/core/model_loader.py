from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


class ModelLoader():
    '''
    Loads selected model into the Wingman
    '''
    def __init__(self, model, apiKey):
        self.model = model
        self.apiKey = apiKey

    def load_model(self):
        models = {'qwen-2.5-32b':ChatGroq, 'llama-3.3-70b-versatile':ChatGroq, 'gpt-3.5':ChatOpenAI, 'gpt4':ChatOpenAI, 'claude3.5-sonnet':ChatAnthropic}

        model_class = models.get(self.model)

        if model_class is None:
            raise ValueError(f'{self.model} is not a valid model.') 
        
        return model_class(model=self.model, api_key=self.apiKey, temperature=0.6)
