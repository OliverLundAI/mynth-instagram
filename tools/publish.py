#!/usr/bin/env python3
"""Publicerar en karusell på Instagram via Instagram API (Instagram Login).

Miljövariabler:
  IG_TOKEN        långlivad åtkomsttoken (krävs)
  IG_API_VERSION  t.ex. v23.0 (valfri; tom = oversionerat anrop)

Kommandon:
  publish.py me                                   -> kontoinfo (user_id, username)
  publish.py refresh                              -> förnyar token, skriver {"access_token","expires_in"}
  publish.py publish <post.json> <url1> <url2>... -> publicerar karusell, skriver {"media_id","permalink"}
  publish.py reel <post.json> <video_url> <cover_url> -> publicerar Reel med eget omslag, skriver {"media_id","permalink"}
  publish.py limit                                -> publiceringskvot senaste 24 h
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

TOKEN = os.environ.get("IG_TOKEN", "").strip()
VER = os.environ.get("IG_API_VERSION", "").strip()
BASE = "https://graph.instagram.com" + (f"/{VER}" if VER else "")


class ApiError(Exception):
    def __init__(self, msg, body):
        super().__init__(msg)
        try:
            self.error = json.loads(body).get("error", {})
        except ValueError:
            self.error = {}


def call(method, path, soft=False, **params):
    params["access_token"] = TOKEN
    url = (path if path.startswith("http") else f"{BASE}/{path.lstrip('/')}")
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        msg = f"API-fel {e.code} på {method} {path}: {body}"
        if soft:
            raise ApiError(msg, body)
        sys.exit(msg)


def me():
    return call("GET", "me", fields="user_id,username,account_type")


def wait_ready(cid, tries=30, pause=4):
    for _ in range(tries):
        r = call("GET", cid, fields="status_code,status")
        st = r.get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {cid} fick status {st}: {r.get('status', '')}")
        time.sleep(pause)
    sys.exit(f"Container {cid} blev aldrig klar")


def publish_container(uid, cid, tries=6, pause=15):
    """media_publish kan svara "not ready" (kod 9007, subkod 2207027) en stund efter att
    containern rapporterat FINISHED. Försök då igen. Samma container kan bara publiceras
    en gång, så omförsök kan inte ge dubbla inlägg."""
    for n in range(1, tries + 1):
        try:
            return call("POST", f"{uid}/media_publish", soft=True, creation_id=cid)["id"]
        except ApiError as e:
            not_ready = e.error.get("code") == 9007 and e.error.get("error_subcode") == 2207027
            if not not_ready or n == tries:
                sys.exit(str(e))
            print(f"Inte klar för publicering, nytt försök om {pause} s ({n}/{tries - 1})", file=sys.stderr)
            time.sleep(pause)


def publish(spec_path, urls):
    post = json.load(open(spec_path, encoding="utf-8"))
    if not 2 <= len(urls) <= 10:
        sys.exit("2–10 bilder krävs för karusell")
    uid = me()["user_id"]
    alts = post.get("alt", [])
    children = []
    for i, u in enumerate(urls):
        p = {"image_url": u, "is_carousel_item": "true"}
        if i < len(alts) and alts[i]:
            p["alt_text"] = alts[i]
        children.append(call("POST", f"{uid}/media", **p)["id"])
    for c in children:
        wait_ready(c)
    parent = call("POST", f"{uid}/media", media_type="CAROUSEL",
                  children=",".join(children), caption=post["caption"])["id"]
    wait_ready(parent)
    mid = publish_container(uid, parent)
    link = call("GET", mid, fields="permalink").get("permalink", "")
    print(json.dumps({"media_id": mid, "permalink": link}))


def reel(spec_path, video_url, cover_url):
    post = json.load(open(spec_path, encoding="utf-8"))
    uid = me()["user_id"]
    cid = call("POST", f"{uid}/media", media_type="REELS", video_url=video_url, cover_url=cover_url,
               caption=post["caption"], share_to_feed="true")["id"]
    wait_ready(cid, tries=72, pause=5)  # videobearbetning tar längre tid än bilder
    mid = publish_container(uid, cid)
    link = call("GET", mid, fields="permalink").get("permalink", "")
    print(json.dumps({"media_id": mid, "permalink": link}))


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("IG_TOKEN saknas")
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "me":
        print(json.dumps(me()))
    elif cmd == "refresh":
        print(json.dumps(call("GET", "https://graph.instagram.com/refresh_access_token",
                              grant_type="ig_refresh_token")))
    elif cmd == "limit":
        print(json.dumps(call("GET", f"{me()['user_id']}/content_publishing_limit", fields="quota_usage,config")))
    elif cmd == "publish":
        publish(sys.argv[2], sys.argv[3:])
    elif cmd == "reel" and len(sys.argv) == 5:
        reel(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
