import requests
import re
from datetime import datetime, timedelta

# Settings
FILENAME = "bein.xml"
DAYS_TO_SCRAPE = 3

# Define the channels we want to include in the header
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

def format_full_date(date_str, time_str, next_day=False):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    if next_day:
        dt += timedelta(days=1)
    clean_time = time_str.strip().replace(':', '')
    return dt.strftime('%Y%m%d') + clean_time + "00"

def scrape():
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
    for c_id, c_name in CHANNELS:
        xml_header += f'  <channel id="{c_id}">\n    <display-name>{c_name}</display-name>\n  </channel>\n'
    
    programme_content = ""
    seen_entries = set() # To prevent duplicates
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    for i in range(0, DAYS_TO_SCRAPE):
        date_str = (datetime.today() + timedelta(days=i)).strftime('%Y-%m-%d')
        for idx in range(0, 4):
            url = f'https://www.bein.com/ar/epg-ajax-template/?action=epg_fetch&category=sports&cdate={date_str}&loadindex={idx}'
            try:
                response = session.get(url, timeout=15)
                data = response.text
                times = re.findall(r'<p\sclass=time>(.*?)<\/p>', data)
                titles = re.findall(r'<p\sclass=title>(.*?)<\/p>', data)
                channels = re.findall(r"data-img.*?sites\/\d+\/\d+\/\d+\/(.*?)\.png", data)

                for j in range(len(titles)):
                    ch_id = channels[j].replace('_Digital_Mono', '').replace('_DIGITAL_Mono', '').replace('-1', '')
                    time_range = times[j].replace('&nbsp;-&nbsp;', '-').split('-')
                    start_t, end_t = time_range[0], time_range[1]
                    
                    # Fix Midnight Wrap-Around
                    is_next_day = int(end_t.replace(':', '')) < int(start_t.replace(':', ''))
                    start_xml = format_full_date(date_str, start_t)
                    end_xml = format_full_date(date_str, end_t, next_day=is_next_day)
                    
                    entry_key = f"{ch_id}{start_xml}"
                    if entry_key not in seen_entries:
                        seen_entries.add(entry_key)
                        title = titles[j].split('- ')[0].strip().replace('&', '&amp;')
                        programme_content += f'  <programme start="{start_xml} +0300" stop="{end_xml} +0300" channel="{ch_id}">\n'
                        programme_content += f'    <title lang="en">{title}</title>\n  </programme>\n'
            except: continue

    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write(xml_header + programme_content + "</tv>")

if __name__ == "__main__":
    scrape()
