"""Signal/Noise → Instagram carousel poster.

Reads social/post.json:
  {"mode": "check" | "post", "issue": "04", "caption": "...", "slides": ["01_cover.jpg", ...]}

check: verifies the token and account, and that every slide URL is reachable. Posts nothing.
post:  publishes the slides as one carousel, then deletes the slides.
Either way it removes post.json and writes the result to social/status.json.
"""
import json, os, sys, time, pathlib, datetime
import requests

API = "https://graph.facebook.com/v23.0"
ROOT = pathlib.Path(__file__).resolve().parent.parent
SOCIAL = ROOT / "social"
POST = SOCIAL / "post.json"
STATUS = SOCIAL / "status.json"

TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
IG_ID = os.environ.get("IG_USER_ID", "").strip()
REPO = os.environ["GITHUB_REPOSITORY"]
SHA = os.environ["GITHUB_SHA"]


def clean(msg):
    return str(msg).replace(TOKEN, "***") if TOKEN else str(msg)


def api(method, path, **params):
    params["access_token"] = TOKEN
    r = requests.request(method, f"{API}/{path}", params=params, timeout=60)
    try:
        data = r.json()
    except ValueError:
        data = {"raw": r.text[:300]}
    if r.status_code >= 400 or "error" in data:
        err = data.get("error", data)
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {clean(err)}")
    return data


def wait_ready(container_id, label, tries=30):
    for _ in range(tries):
        s = api("GET", container_id, fields="status_code,status").get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"{label} container {s}")
        time.sleep(5)
    raise RuntimeError(f"{label} container not ready after {tries * 5}s")


def slide_url(name):
    return f"https://raw.githubusercontent.com/{REPO}/{SHA}/social/{name}"


def main():
    if not POST.exists():
        print("No social/post.json, nothing to do.")
        return
    job = json.loads(POST.read_text(encoding="utf-8"))
    mode = job.get("mode", "check")
    slides = job.get("slides", [])
    status = {"mode": mode, "issue": job.get("issue"), "time": datetime.datetime.utcnow().isoformat() + "Z"}

    try:
        if not TOKEN or not IG_ID:
            raise RuntimeError("IG_ACCESS_TOKEN or IG_USER_ID secret is missing")
        acct = api("GET", IG_ID, fields="id,username")
        status["account"] = acct.get("username")

        urls = [slide_url(n) for n in slides]
        for n, u in zip(slides, urls):
            if not (SOCIAL / n).exists():
                raise RuntimeError(f"slide missing in repo: {n}")
            h = requests.head(u, timeout=30)
            if h.status_code != 200:
                raise RuntimeError(f"slide not reachable ({h.status_code}): {n}")
        status["slides"] = len(slides)

        if mode == "post":
            if not 1 <= len(slides) <= 10:
                raise RuntimeError(f"a post needs 1-10 slides, got {len(slides)}")
            if len(slides) == 1:
                car = api("POST", f"{IG_ID}/media", image_url=urls[0], caption=job.get("caption", ""))["id"]
                wait_ready(car, "image")
            else:
                children = []
                for n, u in zip(slides, urls):
                    c = api("POST", f"{IG_ID}/media", image_url=u, is_carousel_item="true")["id"]
                    wait_ready(c, n)
                    children.append(c)
                car = api("POST", f"{IG_ID}/media", media_type="CAROUSEL",
                          children=",".join(children), caption=job.get("caption", ""))["id"]
                wait_ready(car, "carousel")
            pid = api("POST", f"{IG_ID}/media_publish", creation_id=car)["id"]
            status["post_id"] = pid
            try:
                status["permalink"] = api("GET", pid, fields="permalink").get("permalink")
            except Exception:
                pass
            for n in slides:
                (SOCIAL / n).unlink(missing_ok=True)
        status["ok"] = True
    except Exception as e:
        status["ok"] = False
        status["error"] = clean(e)

    POST.unlink(missing_ok=True)
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if not status["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
