# from AnilistPython import Anilist
# anilist = Anilist()
# print(anilist.get_character('Kyouko Hori'))
# print(anilist.get_anime_with_id(1))

import anilist
query = anilist.get_multiple(name='Shuumatsu Train Doko e Iku?', anime_id=None, page=1)
print(query)

# replace('~', '||'), replace('!', ''), replace('__', '**')
