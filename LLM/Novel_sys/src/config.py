import os
from dotenv import load_dotenv
load_dotenv()

api_key:str= os.getenv("API_KEY","")
base_url:str= os.getenv("BASE_URL","")

model:str= os.getenv("MODEL","deepseek-v4-flash")

outline_temperature:float= float(os.getenv("OUTLINE_TEMPERATURE",0.7))
chaper_temperature:float= float(os.getenv("CHAPER_TEMPERATURE",0.7))
max_tokens:int= int(os.getenv("MAX_TOKENS",1024))
max_retries:int= int(os.getenv("MAX_RETRIES",3))