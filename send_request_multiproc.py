import requests
import json
from multiprocessing import Pool, Lock
import sys
import os

per_page = 200


def search(query, callback, progress_update):
    global done_cnt
    lock = Lock()
    result = {}

    try:
        conf_file_path = "config"
        if getattr(sys, 'frozen', False):
            conf_file_path = os.path.join(sys._MEIPASS, conf_file_path)
        conf = eval(open(conf_file_path, "r").read())
    except Exception:
        conf = {
            'username': 'rdm62865@ebbob.com',
            'password': 'pixivsort_1234'
        }
        open("config", "w").write(str(conf))

    data = {
        'client_id': 'bYGKuGVw91e0NMfPGp44euvGt59s',  # 'bYGKuGVw91e0NMfPGp44euvGt59s',
        'client_secret': 'HP3RmkgAmEGro0gn1x9ioawQE8WMfvLXDz3ZqxpK',
        'grant_type': 'password'
    }
    data.update(conf)

    headers = {
        'Referer': 'http://www.pixiv.net/',
    }
    try:
        f = open("token", "r")
        access_token = f.read().replace("\n", "")
        f.close()
    except Exception:
        access_token = "000000000000000000000"
    headers['Authorization'] = 'Bearer ' + access_token

    mode = 'tag'
    period = 'all'
    sorts = 'date'
    types = ['illustration', 'manga', 'ugoira']
    image_sizes = ['px_480mw', 'px_128x128']
    include_stats = True
    include_sanity_level = True
    params = {
        'q': query,
        'page': 1,
        'per_page': 1,
        'period': period,
        'order': "desc",
        'sort': sorts,
        'mode': mode,
        'types': ','.join(types),
        'include_stats': include_stats,
        'include_sanity_level': include_sanity_level,
        'image_sizes': ','.join(image_sizes),
    }
    pg = json.loads(requests.get('https://public-api.secure.pixiv.net/v1/search/works.json', params=params, headers=headers).text)
    if pg["status"] == "failure":
        del headers["Authorization"]
        r = requests.post('https://oauth.secure.pixiv.net/auth/token', data=data, headers=headers)
        access_token = json.loads(r.text)["response"]["access_token"]
        refresh_token = json.loads(r.text)["response"]["refresh_token"]
        open("token", "w").write(access_token)
        headers['Authorization'] = 'Bearer ' + access_token
        pg = json.loads(requests.get('https://public-api.secure.pixiv.net/v1/search/works.json', params=params, headers=headers).text)
    params["per_page"] = per_page
    total = pg["pagination"]["total"]

    # newest posts
    to_run = round(total/per_page + 0.5)
    if to_run * per_page > 20000:
        to_run = round(20000/per_page+0.5)

    # oldest posts
    to_run2 = max(round((total - to_run*per_page)/per_page + 0.5), 0)
    if to_run2 * per_page > 20000:
        to_run2 = round(20000 / per_page + 0.5)

    pool = Pool(16)
    done_cnt = 0

    def res_append(res):
        global done_cnt
        lock.acquire()
        done_cnt += 1
        print("done #"+str(done_cnt))
        result.update(res)
        progress_update(done_cnt, to_run+to_run2)
        lock.release()
    for i in range(1, to_run+1):
        pool.apply_async(req, (query, i, params, headers), callback=res_append)

    if to_run2 != 0:
        params = params.copy()
        params["order"] = "asc"
        for i in range(1, to_run + 1):
            pool.apply_async(req, (query, i, params, headers), callback=res_append)
    pool.close()
    pool.join()
    callback(sorted(list(result.values()), key=lambda x: x[4], reverse=True))


# post - (id, preview_480, preview_128, page_count, favorite_count)
def req(query, page, params, headers):
    params["page"] = page

    res = json.loads(requests.get('https://public-api.secure.pixiv.net/v1/search/works.json', params=params, headers=headers).text)
    arr = {}
    for i in res["response"]:
        arr[i['id']] = (i['id'], i['image_urls']['px_480mw'], i['image_urls']['px_128x128'], i['page_count'], (i['stats']['favorited_count']['public'] + i['stats']['favorited_count']['private']))
    return arr