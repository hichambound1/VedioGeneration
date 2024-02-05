from datetime import datetime


def create_log(text):
    now = datetime.now()
    file_path = (
        "/var/log/videos/"
        + str(now.year)
        + "-"
        + str(now.month)
        + "-"
        + str(now.day)
        + ".log"
    )
    with open(file_path, "a") as fp:
        fp.write(text + "\n")
