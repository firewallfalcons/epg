import requests
import re
from datetime import datetime, timedelta

# Settings
FILENAME = "bein.xml"
DAYS_TO_SCRAPE = 3
POST_ID = "25344"
SERVICE_ID = "bein.net"

# Channel IDs
CHANNELS = [
    ("beIN_SPORTS1", "beIN Sports 1"), ("beIN_SPORTS2", "beIN Sports 2"),
    ("beIN_SPORTS3", "beIN Sports 3"), ("beIN_SPORTS4", "beIN Sports 4"),
    ("beIN_SPORTS5", "beIN Sports 5"), ("beIN_SPORTS6-d", "beIN Sports 6"),
    ("beIN_SPORTS7", "beIN Sports 7"), ("logos-_beINSPORTS8", "beIN Sports 8"),
    ("logos-_beINSPORTS9", "beIN Sports 9"), ("2023_Alkass_1", "Alkass 1"),
    ("2023_Alkass_2", "Alkass 2"), ("2023_Alkass_3", "Alkass 3"),
    ("2023_Alkass_4", "Alkass 4"), ("2023_Alkass_5", "Alkass 5"),
    ("2023_Alkass_6", "Alkass 6")
]

def format_date(date_str, time_str, next_day=False):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    if next_day:
        dt += timedelta(days=1)
    return dt.strftime("%Y%m%d%H%M%S")

def scrape():
    print("Starting beIN EPG Scraper (NO TIME SHIFT)...")

    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_header += '<tv generator-info-name="beIN Scraper">\n'

    for cid, cname in CHANNELS:
        xml_header += f'  <channel id="{cid}">\n'
        xml_header += f'    <display-name>{cname}</display-name>\n'
        xml_header += '  </channel>\n'

    programme_content = ""
    seen = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    for d in range(DAYS_TO_SCRAPE):
        date_str = (datetime.today() + timedelta(days=d)).strftime("%Y-%m-%d")

        for idx in range(4):
            url = (
                "https://www.bein.com/ar/epg-ajax-template/"
                f"?action=epg_fetch&category=sports&serviceidentity={SERVICE_ID}"
                f"&offset=00&mins=00&cdate={date_str}"
                f"&language=AR&postid={POST_ID}&loadindex={idx}"
            )

            try:
                r = session.get(url, timeout=20)
                html = r.text

                times = re.findall(r'<p\sclass=time>(.*?)<\/p>', html)
                titles = re.findall(r'<p\sclass=title>(.*?)<\/p>', html)
                descs = re.findall(r'<p\sclass=format>(.*?)<\/p>', html)
                channels = re.findall(
                    r"sites\/\d+\/\d+\/\d+\/(.*?)\.png", html
                )

                count = min(len(times), len(titles), len(channels))

                for i in range(count):
                    ch_id = (
                        channels[i]
                        .replace("_Digital_Mono", "")
                        .replace("_DIGITAL_Mono", "")
                        .replace("-1", "")
                    )

                    t = times[i].replace("&nbsp;-&nbsp;", "-").split("-")
                    if len(t) != 2:
                        continue

                    start_t, end_t = t
                    next_day = int(end_t.replace(":", "")) < int(start_t.replace(":", ""))

                    start_xml = format_date(date_str, start_t)
                    end_xml = format_date(date_str, end_t, next_day)

                    key = f"{ch_id}{start_xml}"
                    if key in seen:
                        continue
                    seen.add(key)

                    title = titles[i].split("- ")[0].strip().replace("&", "&amp;")
                    desc = descs[i].strip().replace("&", "&amp;") if i < len(descs) else ""

                    programme_content += (
                        f'  <programme start="{start_xml}" stop="{end_xml}" channel="{ch_id}">\n'
                        f'    <title lang="en">{title}</title>\n'
                    )

                    if desc:
                        programme_content += f'    <desc lang="ar">{desc}</desc>\n'

                    programme_content += "  </programme>\n"

            except Exception as e:
                continue

    full_xml = xml_header + programme_content + "</tv>"

    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write(full_xml)

    print(f"EPG saved correctly as {FILENAME} (NO DELAY)")

if __name__ == "__main__":
    scrape()
