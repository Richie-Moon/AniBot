# from AnilistPython import Anilist
# anilist = Anilist()
# print(anilist.get_character('Kyouko Hori'))
# print(anilist.get_anime_with_id(1))

import anilist
from os import environ
from dotenv import load_dotenv
import pymongo

load_dotenv()
PASSWORD = environ['PASSWORD']

client = pymongo.MongoClient(f"mongodb+srv://CSA:{PASSWORD}@anibot.o2nqcvj.mongodb.net/?retryWrites=true&w=majority")

db = client['test_db']
collection = db['test_collection']
post = {'_id': 'test', 'name': 'Richie'}

# collection.insert_one(post)

print(anilist.get_multiple(name='one piece', status='RELEASING'))

# replace('~', '||'), replace('!', ''), replace('__', '**')
