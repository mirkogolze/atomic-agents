import openai
import os

from deep_research.config import ChatConfig

# Setzen Sie Ihre Azure OpenAI-Endpoint-URL und den Namen des Modells
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_DEPLOYMENT") 
api_key = os.getenv("AZURE_API_KEY") 

if (ChatConfig.use_azure):
    client = openai.AzureOpenAI(azure_endpoint=azure_openai_endpoint, azure_deployment=deployment_name, api_key=api_key, api_version="2023-05-15")
else:
    if (ChatConfig.base_url):
        client = openai.OpenAI(api_key=ChatConfig.api_key, base_url=ChatConfig.base_url)
    else:
        client = openai.OpenAI(api_key=ChatConfig.api_key)