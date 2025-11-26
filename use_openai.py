from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.keyvault.secrets import SecretClient
import openai

VAULT_URL = "https://projectanalysis2.vault.azure.net/"
SECRET_NAME = "openai-key"

cred = InteractiveBrowserCredential()      # local
# cred = DefaultAzureCredential()          # when deployed in Azure
client = SecretClient(vault_url=VAULT_URL, credential=cred)
openai.api_key = client.get_secret(SECRET_NAME).value
