import requests
import re
from datetime import datetime, timedelta

# Settings
FILENAME = "bein.xml"
DAYS_TO_SCRAPE = 3
POST_ID = "25344"
SERVICE_ID = "bein.net"

# Channel IDs for the header
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
    dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
    if next_day:
        dt += timedelta(days=1)
    return dt.strftime('%Y%m%d%H%M%S')

def scrape():
    print("Starting beIN EPG Scraper (Fixed Time & Midnight Wrap)...")
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="GitHub beIN Scraper">\n'
    for c_id, c_name in CHANNELS:
        xml_header += f'  <channel id="{c_id}">\n    <display-name>{c_name}</display-name>\n  </channel>\n'
    
    programme_content = ""
    seen_entries = set()
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    for i in range(0, DAYS_TO_SCRAPE):
        date_str = (datetime.today() + timedelta(days=i)).strftime('%Y-%m-%d')
        for idx in range(0, 4):
            url = f"https://www.bein.com/ar/epg-ajax-template/?action=epg_fetch&category=sports&serviceidentity={SERVICE_ID}&offset=00&mins=00&cdate={date_str}&language=AR&postid={POST_ID}&loadindex={idx}"
            try:
                response = session.get(url, timeout=20)
                data = response.text
                times_raw = re.findall(r'<p\sclass=time>(.*?)<\/p>', data)
                titles_raw = re.findall(r'<p\sclass=title>(.*?)<\/p>', data)
                descs_raw = re.findall(r'<p\sclass=format>(.*?)<\/p>', data)
                channels_raw = re.findall(r"data-img.*?sites\/\d+\/\d+\/\d+\/(.*?)\.png", data)

                count = min(len(times_raw), len(titles_raw), len(channels_raw))
                for j in range(count):
                    ch_id = channels_raw[j].replace('_Digital_Mono', '').replace('_DIGITAL_Mono', '').replace('-1', '')
                    time_range = times_raw[j].replace('&nbsp;-&nbsp;', '-').split('-')
                    if len(time_range) < 2: continue
                    
                    start_t, end_t = time_range[0], time_range[1]
                    
                    # FIXED: Check if program ends after midnight (e.g. 23:00 to 01:00)
                    is_next_day = int(end_t.replace(':', '')) < int(start_t.replace(':', ''))
                    
                    start_xml = format_date(date_str, start_t)
                    end_xml = format_date(date_str, end_t, next_day=is_next_day)
                    
                    entry_key = f"{ch_id}{start_xml}"
                    if entry_key not in seen_entries:
                        seen_entries.add(entry_key)
                        clean_title = titles_raw[j].split('- ')[0].strip().replace('&', '&amp;')
                        clean_desc = descs_raw[j].strip().replace('&', '&amp;') if j < len(descs_raw) else ""
                        
                        # Use your phone's timezone offset (+0200) so the app doesn't shift it
                        entry =  f'  <programme start="{start_xml} +0300" stop="{end_xml} +0300" channel="{ch_id}">\n'
                        entry += f'    <title lang="en">{clean_title}</title>\n'
                        if clean_desc:
                            entry += f'    <desc lang="ar">{clean_desc}</desc>\n'
                        entry += '  </programme>\n'
                        programme_content += entry
            except: continue

    full_xml = xml_header + programme_content + "</tv>"
    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write(full_xml)
    print(f"Successfully saved {FILENAME} for Cairo Offset.")

if __name__ == "__main__":
    scrape()
