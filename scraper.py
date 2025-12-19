import requests
import re
import os
from datetime import datetime, timedelta

# Settings
FILENAME = "bein.xml"
DAYS_TO_SCRAPE = 3

def format_epg_date(date_str, time_str):
    if not time_str: return ""
    # beIN returns time as "HH:mm"
    parts = time_str.strip().split(':')
    year_month_day = date_str.replace('-', '')
    return f"{year_month_day}{parts[0].zfill(2)}{parts[1].zfill(2)}00"

def scrape():
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<tv generator-info-name="GitHub beIN Scraper">\n'
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    for i in range(0, DAYS_TO_SCRAPE):
        date_str = (datetime.today() + timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Loop through the 4 data batches beIN provides
        for idx in range(0, 4):
            url = f'https://www.bein.com/ar/epg-ajax-template/?action=epg_fetch&category=sports&serviceidentity=bein.net&offset=00&mins=00&cdate={date_str}&language=AR&postid=25344&loadindex={idx}'
            
            try:
                response = session.get(url, timeout=15)
                data = response.text
                
                # Regex Extraction
                times_raw = re.findall(r'<p\sclass=time>(.*?)<\/p>', data)
                titles = re.findall(r'<p\sclass=title>(.*?)<\/p>', data)
                formats = re.findall(r'<p\sclass=format>(.*?)<\/p>', data)
                channels = re.findall(r"data-img.*?sites\/\d+\/\d+\/\d+\/(.*?)\.png", data)
                lives = re.findall(r"li\s+live='(\d)'", data)

                for j in range(len(titles)):
                    try:
                        # Clean channel name to match your M3U tvg-id
                        ch_id = channels[j].replace('_Digital_Mono', '').replace('_DIGITAL_Mono', '').replace('-1', '')
                        
                        # Time parsing
                        time_split = times_raw[j].replace('&nbsp;-&nbsp;', '-').split('-')
                        start_xml = format_epg_date(date_str, time_split[0])
                        end_xml = format_epg_date(date_str, time_split[1])
                        
                        # Title and Description
                        title_main = titles[j].split('- ')[0].strip().replace('&', 'and')
                        desc_match = re.search(r'-\s(.*)', titles[j])
                        description = desc_match.group(1).replace('&', 'and') if desc_match else titles[j].replace('&', 'and')
                        
                        is_live = "Live: " if lives[j] == "1" else ""
                        fmt_info = formats[j].replace('2014', '2021') if j < len(formats) else ""

                        entry =  f'  <programme start="{start_xml} +0300" stop="{end_xml} +0300" channel="{ch_id}">\n'
                        entry += f'    <title lang="en">{is_live}{title_main} - {fmt_info}</title>\n'
                        entry += f'    <desc lang="ar">{description.strip()}</desc>\n'
                        entry += f'  </programme>\n'
                        xml_content += entry
                    except:
                        continue
            except Exception as e:
                print(f"Error on {date_str} index {idx}: {e}")

    xml_content += '</tv>'
    
    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"Successfully saved {FILENAME}")

if __name__ == "__main__":
    scrape()
