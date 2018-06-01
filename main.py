import requests
import bs4
import queue
import threading
from multiprocessing.dummy import Pool

base = 'http://briannawu2018.com'
n = 2
cores = 8
pool = Pool(cores)
seen_set = set()
to_see_set = set('/')
seen_queue = queue.Queue()
to_see_queue = queue.Queue()


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def seen_daemon():
    while True:
        msg = seen_queue.get(block=True)
        seen_set.add(msg)


def to_see_daemon():
    global to_see_set
    while True:
        op, msg = to_see_queue.get(block=True)
        if op:
            to_see_set = to_see_set.difference(set(msg))
        else:
            to_see_set.add(msg)


def get(path):
    body = requests.get("%s%s" % (base, path)).text
    doc = bs4.BeautifulSoup(body, "html.parser")

    seen_queue.put(path)
    to_see_queue.put((True, path), block=False)

    for a_href in doc.findAll('a', href=True):
        href = a_href['href']
        if not href.startswith(base) and not href.startswith('/'):
            continue
        if href in seen_set is not None:
            continue
        if href.startswith("//"):
            continue

        if href.startswith(base):
            href = remove_prefix(href, base)

        to_see_queue.put((False, href))


def main():
    threading.Thread(target=seen_daemon, daemon=True).start()
    threading.Thread(target=to_see_daemon, daemon=True).start()

    for i in range(n):
        if len(to_see_set) > 0:
            pool.map(get, to_see_set.copy())

    for link in to_see_set.union(seen_set):
        print(link)


main()
