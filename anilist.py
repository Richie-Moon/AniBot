import requests
import json

url = 'https://graphql.anilist.co'


def get_multiple(name, anime_id, page: int):
    query = """
        query ($search: String, $id: Int, $page: Int, $perpage: Int) {
            Page (page: $page, perPage: $perpage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
            

                media (search: $search, type: ANIME, id: $id) {
                    id
                    title {
                        romaji
                        english
                    }
                }
            }
        }   
    """

    variables = {'perpage': 25}
    if anime_id is not None:
        variables['id'] = anime_id
    if name is not None:
        variables['search'] = name
    variables['page'] = page

    response = json.loads(requests.post(url, json={'query': query, 'variables': variables}).text)
    data = response['data']['Page']

    if data is not None:
        if len(data['media']) == 0:
            return [{'Not Found', 404}]
        elif len(data['media']) == 1 and data['pageInfo']['lastPage'] == 1:
            return get_anime(data['media'][0]['id'])
        else:
            return data
    else:
        return response['errors']


def get_anime(anime_id: int):
    query = """
        query ($id: Int) {
            Media (type: ANIME, id: $id) {
                id
                title {
                    romaji
                    english
                }
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                coverImage {
                    large
                    color
                }
                bannerImage
                format
                status
                episodes
                duration
                season
                description
                averageScore
                genres
                nextAiringEpisode {
                    airingAt
                    timeUntilAiring
                    episode
                }
                isAdult
                countryOfOrigin
            }
        }
"""
    variables = {'id': anime_id}

    response = json.loads(requests.post(url, json={'query': query, 'variables': variables}).text)
    print(response)
    data = response['data']['Media']

    if data is not None:

        _id = data['id']

        name_romaji = data['title']['romaji']
        name_english = data['title']['english']

        start_date = f"{data['startDate']['day']}/{data['startDate']['month']}/{data['startDate']['year']}"
        end_date = f"{data['endDate']['day']}/{data['endDate']['month']}/{data['endDate']['year']}"

        cover_image = data['coverImage']['large']
        banner_image = data['bannerImage']
        cover_color = data['coverImage']['color']

        airing_format = data['format']
        airing_status = data['status']
        airing_episodes = data['episodes']
        next_airing_episode = data['nextAiringEpisode']
        season = data['season']
        episode_duration = data['duration']

        description = data['description']
        average_score = data['averageScore']
        genres = data['genres']

        is_adult = data['isAdult']
        origin_country = data['countryOfOrigin'].lower()

        formatted_data = {'_id': _id, 'name_romaji': name_romaji, 'name_english': name_english, 'start_date': start_date, 'end_date': end_date, 'cover_image': cover_image,
                          'banner_image': banner_image, 'cover_color': cover_color, 'airing_format': airing_format, 'airing_status': airing_status, 'airing_episodes': airing_episodes,
                          'next_airing_episode': next_airing_episode, 'season': season, 'episode_duration': episode_duration, 'desc': description, 'average_score': average_score,
                          'genres': genres, 'is_adult': is_adult, 'origin_country': origin_country}

        return formatted_data

    else:
        return response['errors']