import argparse
import concurrent.futures
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

import requests

import pyperclip


def download(username, singleStory=False):
    if singleStory:
        api = "https://storysharing.snapchat.com/v1/fetch/s:{}?request_origin=ORIGIN_WEB_PLAYER"
    else:
        api = "https://storysharing.snapchat.com/v1/fetch/{}?request_origin=ORIGIN_WEB_PLAYER"

    url = api.format(username)
    response = requests.get(url)

    if response.status_code != 200:
        print("\033[91m[-] {} hs no stories\033[0m".format(username))
        return

    data = response.json()
    # Using dict.get() will return None when there are no snaps instead of throwing a KeyError
    story_arr = data.get("story").get("snaps")

    if story_arr:
        print(
            "\033[92m[+] {} has {} stories\033[0m".format(username, len(story_arr)))
        story_type = data.get("story").get("metadata").get("storyType")
        title = data.get("story").get("metadata").get("title")

        # TYPE_PUBLIC_USER_STORY = Story from a user
        # There are many different story types.
        if story_type == "TYPE_PUBLIC_USER_STORY":
            username = data["story"]["id"]
            # print("\33[93m[!] Downloading stories for {} {} (\033[91m{}\33[93m)\33[0m".format(
            #     title, str(data["story"]["metadata"]["emoji"]), username
            # ))
        else:
            # print("\33[93m[!] Downloading stories from", title)
            # If dont do this the folder will be have a long
            # unidentifiable name. So we are using the title
            # as the "username"
            username = title.replace(" ", "_")

        # Making a directory with given username
        # to store the images of that user
        os.makedirs(username, exist_ok=True)
        for index, media in enumerate(story_arr):
            try:
                file_url = media["media"]["mediaUrl"]
                timestamp = int(media["captureTimeSecs"])
                date = datetime.utcfromtimestamp(
                    timestamp).strftime('%Y-%m-%d')

                # We cant download images anymore. Its not in the JSON
                # response. But I just commented it out incase it comes
                # back.
                if media["media"]["type"] == "IMAGE":
                    file_ext = ".jpg"
                if media["media"]["type"] == "VIDEO":
                    file_ext = ".mp4"
                elif media["media"]["type"] == "VIDEO_NO_SOUND":
                    file_ext = ".mp4"

                dir_name = os.path.join(username, date)

                os.makedirs(dir_name, exist_ok=True)

                filename = datetime.utcfromtimestamp(timestamp).strftime(
                    '%Y-%m-%d_%H-%M-%S {} {}{}'.format(media.get("id"),
                                                       username, file_ext)
                )
                path = os.path.join(dir_name, filename)

                if not os.path.exists(path):
                    urllib.request.urlretrieve(file_url, path)
                    print("\033[92m[+] Downloading story ({:d}/{:d}):\033[0m {:s}".format(
                        index+1, len(story_arr), filename))
                    # We need a small pause or else we will get a ConnectionResetError
                    time.sleep(0.3)
                else:
                    print("\33[93m[!] {} Story ({:d}/{:d}) already exists:\033[0m {:s}".format(
                        username, index+1, len(story_arr), filename))
            except KeyError as e:
                print(
                    "\033[91m[-] Could not get file data: \033[0m{:s}".format(str(e)))
            except KeyboardInterrupt:
                print("\033[91m[!] Download cancelled\033[0m")
                break
    else:
        print("\033[91m[-] {} hs no stories\033[0m".format(username))


def main():
    parser = argparse.ArgumentParser(
        description="A public SnapChat story downloader")
    parser.add_argument('usernames', action="store", nargs="*",
                        help="The username or id of a public story")

    parser.add_argument('-c', '--clipboard', action="store_true",
                        help="Scan usernames from Clipboard\nFORMAT: https://story.snapchat.com/s/<username>")

    parser.add_argument('-s', '--single', action="store_true",
                        help="Download a single story")

    args = parser.parse_args()

    if args.clipboard:
        history = list()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            while True:
                for username in re.findall('https://story.snapchat.com/s/([\w_\.]+)', pyperclip.paste()):
                    if username not in history:
                        executor.submit(download, username, args.single)
                        history.append(username)
                time.sleep(1)
    else:
        for username in args.usernames:
            download(username, singleStory=args.single)


if __name__ == "__main__":
    main()
