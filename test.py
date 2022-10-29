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

client = pymongo.MongoClient(f"mongodb+srv://CSA:{PASSWORD}@anibot.o2nqcvj.mongodb.net/?retryWrites=true&w=majority")

db = client['release_tracking']
collection = db['792309472784547850']
test = db['test']


# query ($name: String = "Levi", $page: Int = 1) {
#   Page (page: $page) {
#     pageInfo {
#       total
#       currentPage
#
#     }
#     characters(search: $name) {
#       id
#       name {
#         full
#       }
#       description (asHtml: false)
#       dateOfBirth
#       gender
#       age
#       siteUrl
#       media {
#         edges {
#           node {
#             title {
#               english
#               romaji
#             }
#             type
#           }
#         }
#       }
#     }
#   }
# }

print(anilist.get_character(66171))


# replace('~', '||'), replace('!', ''), replace('__', '**')
