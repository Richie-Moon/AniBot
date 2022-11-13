# from AnilistPython import Anilist
# anilist = Anilist()
# print(anilist.get_character('Kyouko Hori'))
# print(anilist.get_anime_with_id(1))
import string

import anilist
from os import environ
from dotenv import load_dotenv
import pymongo
import json
import requests

load_dotenv()
PASSWORD = environ['PASSWORD']

# client = pymongo.MongoClient(f"mongodb+srv://CSA:{PASSWORD}@anibot.o2nqcvj.mongodb.net/?retryWrites=true&w=majority")
#
# db = client['release_tracking']
# collection = db['792309472784547850']
# test = db['test']
#

print(anilist.get_next_airing_episode(97940))


# replace('~', '||'), replace('!', ''), replace('__', '**')
