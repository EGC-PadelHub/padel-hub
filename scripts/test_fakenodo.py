import os
import sys
import time
import json
import requests

BASE = os.environ.get("FAKENODO_URL", "http://127.0.0.1:5055/api/deposit/depositions")


def main():
    print(f"Using base: {BASE}")

    # 1) Create deposition
    r = requests.post(BASE, json={"metadata": {"title": "TestDepo", "upload_type": "dataset"}})
    assert r.status_code == 201, r.text
    depo = r.json()
    depo_id = depo["id"]
    print("Created deposition:", json.dumps(depo, indent=2))

    # 2) Upload file
    files_url = f"{BASE}/{depo_id}/files"
    with open(__file__, "rb") as f:
        r = requests.post(files_url, data={"name": "testfile.txt"}, files={"file": f})
    assert r.status_code == 201, r.text
    print("Uploaded file:", r.json())

    # 3) First publish
    pub_url = f"{BASE}/{depo_id}/actions/publish"
    r = requests.post(pub_url)
    assert r.status_code == 202, r.text
    first_pub = r.json()
    print("First publish:", json.dumps(first_pub, indent=2))

    # 4) Update metadata only and publish again (should keep DOI)
    put_url = f"{BASE}/{depo_id}"
    r = requests.put(put_url, json={"metadata": {"title": "Updated title"}})
    assert r.status_code == 200, r.text
    r = requests.post(pub_url)
    assert r.status_code == 202, r.text
    second_pub = r.json()
    print("Second publish (metadata only):", json.dumps(second_pub, indent=2))
    assert first_pub["doi"] == second_pub["doi"], "DOI changed but files did not"

    # 5) Change files and publish again (should bump DOI)
    with open(__file__, "rb") as f:
        r = requests.post(files_url, data={"name": "another.txt"}, files={"file": f})
    assert r.status_code == 201, r.text
    r = requests.post(pub_url)
    assert r.status_code == 202, r.text
    third_pub = r.json()
    print("Third publish (with file change):", json.dumps(third_pub, indent=2))
    assert third_pub["doi"] != second_pub["doi"], "DOI did not change after files changed"

    # 6) List versions
    vers_url = f"{BASE}/{depo_id}/versions"
    r = requests.get(vers_url)
    assert r.status_code == 200, r.text
    print("Versions:", json.dumps(r.json(), indent=2))

    print("All checks passed 🎉")


if __name__ == "__main__":
    main()
