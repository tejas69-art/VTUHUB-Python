from fastapi import FastAPI, HTTPException
from models.requests.models import SingleRequest, RangeRequest
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib3
import re
import json

from services.mainclass import VTUScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="VTU Scraper API")


# ----------------- HEALTH CHECK -----------------
@app.get("/health")
def health():
    """Health check endpoint for deployment platforms"""
    return {"status": "ok", "service": "VTU Scraper API"}


# ----------------- SINGLE POST API -----------------
@app.post("/single-post")
def single_post(body: SingleRequest):
    url = body.index_url.strip()

    # extract site path inline
    m = re.search(r"results\.vtu\.ac\.in/([^/]+)/index\.php", url)
    if not m:
        raise HTTPException(400, "Invalid index_url format")
    site_path = m.group(1)

    scraper = VTUScraper(site_path)

    MAX_RETRY = 5
    attempt = 0
    result = None

    while attempt < MAX_RETRY:
        attempt += 1
        print(f"[SINGLE] Attempt {attempt}")

        try:
            # try all allowed signatures
            try:
                result = scraper.run(lns=body.usn)
            except TypeError:
                try:
                    result = scraper.run(Ins=body.usn)
                except TypeError:
                    result = scraper.run(body.usn)

        except Exception as e:
            raise HTTPException(500, str(e))

        # convert to HTML string
        html = result["html"] if isinstance(result, dict) and "html" in result else str(result)

        # INVALID CAPTCHA CHECK
        if "Invalid captcha" in html or "Invalid captcha code !!!" in html:
            print("Invalid captcha — retrying...")
            continue

        # valid result → break
        break

    return {"usn": body.usn, "html": html}


# ----------------- RANGE POST API -----------------
@app.post("/range-post")
def range_post(body: RangeRequest):
    url = body.index_url.strip()

    m = re.search(r"results\.vtu\.ac\.in/([^/]+)/index\.php", url)
    if not m:
        raise HTTPException(400, "Invalid index_url format")
    site_path = m.group(1)

    # inline USN pattern
    m1 = re.search(r"^(.*?)(\d+)$", body.start_usn)
    m2 = re.search(r"^(.*?)(\d+)$", body.end_usn)
    if not m1 or not m2:
        return {"error": "Cannot auto-increment USN format"}

    prefix = m1.group(1)
    start_num = int(m1.group(2))
    end_num = int(m2.group(2))
    width = len(m1.group(2))

    if end_num < start_num:
        return {"error": "End USN must be >= Start USN"}

    # concurrency settings
    MAX_WORKERS = 10

    def fetch_usn(usn: str) -> (str, str):
        """
        Worker for a single USN.
        Returns tuple (usn, html_or_error)
        """
        MAX_RETRY = 5
        attempt = 0
        last_err = None

        # create a fresh scraper per worker for thread-safety
        scraper = VTUScraper(site_path)

        while attempt < MAX_RETRY:
            attempt += 1
            print(f"[RANGE][{usn}] Attempt {attempt}")

            try:
                try:
                    res = scraper.run(lns=usn)
                except TypeError:
                    try:
                        res = scraper.run(Ins=usn)
                    except TypeError:
                        res = scraper.run(usn)
            except Exception as e:
                last_err = json.dumps({"error": str(e)})
                # fatal error for this USN: stop retrying
                return usn, last_err

            html = res["html"] if isinstance(res, dict) and "html" in res else str(res)

            # check captcha fail -> retry
            if "Invalid captcha" in html or "Invalid captcha code !!!" in html:
                print(f"[RANGE][{usn}] Invalid captcha — retrying...")
                continue

            # success
            return usn, html

        # all retries exhausted
        return usn, "FAILED AFTER 5 RETRIES (CAPTCHA ERROR)" if last_err is None else last_err

    # prepare USN list
    usn_list = [f"{prefix}{str(n).zfill(width)}" for n in range(start_num, end_num + 1)]

    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_usn, usn): usn for usn in usn_list}
        for fut in as_completed(futures):
            usn = futures[fut]
            try:
                u, output = fut.result()
                results[u] = output
            except Exception as e:
                results[usn] = json.dumps({"error": str(e)})

    return results
