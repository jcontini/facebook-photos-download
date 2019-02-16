import argparse, sys, os, time, wget, json, piexif, ssl, urllib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
from dateutil.parser import parse
from datetime import datetime
from datetime import timedelta

def start_session(username, password):
    print("Opening Browser...")
    wd_options = Options()
    wd_options.add_argument("--disable-notifications")
    wd_options.add_argument("--disable-infobars")
    wd_options.add_argument("--mute-audio")
    wd_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(chrome_options=wd_options)

    #Login
    driver.get("https://www.facebook.com/")
    print("Logging In...")
    email_id = driver.find_element_by_id("email")
    pass_id = driver.find_element_by_id("pass")
    email_id.send_keys(username)
    pass_id.send_keys(password)
    driver.find_element_by_id("loginbutton").click()

    return driver

def index_photos():
    #Set waits (go higher if slow internet)
    wait = WebDriverWait(driver, 10)
    main_wait = 1
    stuck_wait = 3

    #Nav to photos I'm tagged in page
    print("Navigating to photos of you...")
    profile_url = driver.find_elements_by_css_selector('[data-type="type_user"] a:nth-child(2)')[0].get_attribute("href")
    photos_url = 'https://www.facebook.com' + profile_url.split('com')[1].split('?')[0] + "/photos_of"
    driver.get(photos_url)
    print("Scanning Photos...")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "uiMediaThumbImg")))
    driver.find_elements_by_css_selector(".uiMediaThumbImg")[0].click()
    time.sleep(2)

    #Prep structure
    data = {}
    data['tagged'] = []

    while True:
        time.sleep(main_wait)
        try:
            user = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftAuthorName"]//a')))
            media_url = wait.until(EC.presence_of_element_located((By.XPATH, "//img[@class='spotlight']"))).get_attribute('src')
            is_video = "showVideo" in driver.find_element_by_css_selector(".stageWrapper").get_attribute("class")
        except exceptions.StaleElementReferenceException:
            continue

        doc = {
            'fb_url': driver.current_url,
            'fb_date': wait.until(EC.presence_of_element_located((By.CLASS_NAME, "timestampContent"))).text,
            'fb_caption': wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftCaption"]'))).text,
            'fb_tags': wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="fbPhotoSnowliftTagList"]'))).text.replace('\u2014 ',''),
            'media_url': media_url,
            'media_type': 'video' if is_video else 'image',
            'user_name': user.text,
            'user_url': user.get_attribute('href'),
            'user_id': user.get_attribute('data-hovercard').split('id=')[1].split('&')[0]
        }

        #Check to see if photo didn't refresh or if last photo
        if len(data['tagged'])>0:
            if (doc['media_type'] == 'image') and (data['tagged'][-1]['media_url'] == doc['media_url']):
                print("Photo stuck. Waiting %s seconds..." % (stuck_wait),end="",flush=True)
                time.sleep(stuck_wait)
                photo_now = driver.find_element(By.XPATH, "//img[@class='spotlight']").get_attribute('src')
                if data['tagged'][-1]['media_url'] == photo_now:
                    print("Still stuck. Clicking Next again...",end="",flush=True)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".snowliftPager.next"))).click()
                    print("Got it. Scanning the page again...")
                    continue
                print('OK, that worked. Moving on...')

            if driver.current_url == data['tagged'][0]['fb_url']:
                print("-"*20 + "Done Indexing! Last Photo: %s" % (driver.current_url))
                break

        #Get album if present
        if len(driver.find_elements_by_xpath('//*[@class="fbPhotoMediaTitleNoFullScreen"]/div/a')) > 0:
            doc['album'] = driver.find_element_by_xpath('//*[@class="fbPhotoMediaTitleNoFullScreen"]/div/a').get_attribute('href')

        #Get Deets & move on
        print("%s) %s // %s" % (len(data['tagged'])+1, doc['fb_date'],doc['fb_tags']))
        data['tagged'].append(doc)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".snowliftPager.next"))).click()

        #Save JSON deets
        with open('tagged.json', 'w') as f:
            json.dump(data, f, indent=4)
        f.close()

def download_photos():
    ssl._create_default_https_context = ssl._create_unverified_context
    #Prep the download folder
    folder = 'photos/'
    if not os.path.exists(folder):
        os.makedirs(folder)
    print("Saving photos to " + folder)
    #Download the photos
    with open('tagged.json') as json_file:
        data = json.load(json_file)
        for i,d in enumerate(data['tagged']):
            if d['media_type'] == 'image':
                #Save new file
                if d['fb_date'] == "Today":
                    filename_date = datetime.today().strftime('%Y-%m-%d')
                elif d['fb_date'] == "Yesterday":
                    filename_date = datetime.today() - timedelta(days=1)
                    filename_date = filename_date.strftime('%Y-%m-%d')
                else:
                    filename_date = parse(d['fb_date']).strftime("%Y-%m-%d")
                img_id = d['media_url'].split('_')[1]
                new_filename = folder + filename_date + '_' + img_id + '.jpg'
                if os.path.exists(new_filename):
                    print("Already Exists (Skipping): %s" % (new_filename))
                else:
                    delay = 1

                    while True:
                        try:
                            print("Downloading " + d['media_url'])
                            img_file = wget.download(d['media_url'], new_filename, False)
                            break
                        except (TimeoutError, urllib.error.URLError) as e:
                            print("Sleeping for {} seconds".format(delay))
                            time.sleep(delay)
                            delay *= 2
                    #Update EXIF Date Created
                    exif_dict = piexif.load(img_file)
                    if d['fb_date'] == "Today":
                        exif_date = datetime.today().strftime("%Y:%m:%d %H:%M:%S")
                    elif d['fb_date'] == "Yesterday":
                        exif_date = datetime.today() - timedelta(days=1)
                        exif_date = exif_date.strftime("%Y:%m:%d %H:%M:%S")
                    else:
                        exif_date = parse(d['fb_date']).strftime("%Y:%m:%d %H:%M:%S")
                    img_desc = d['fb_caption'] + '\n' + d['fb_tags'] + '\n' + d['fb_url'].split("&")[0]
                    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date
                    exif_dict['0th'][piexif.ImageIFD.Copyright] = (d['user_name'] + ' (' + d['user_url']) + ')'
                    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = img_desc.encode('utf-8')

                    piexif.insert(piexif.dump(exif_dict), img_file)
                    print(str(i+1) + ') Added '+ new_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook Scraper')
    parser.add_argument('-u', type = str,help='FB Username')
    parser.add_argument('-p', type = str,help='FB Password')
    parser.add_argument('--download', action='store_true', help='Download photos only')
    parser.add_argument('--index', action='store_true', help='Index photos')
    args = parser.parse_args()
    try:
        if args.download:
            download_photos()
        else:
            if not (args.u and args.p):
                print('Please try again with FB credentials (use -u -p)')
            else:
                driver = start_session(args.u,args.p)
                index_photos()
                if not args.index:
                    download_photos()
    except KeyboardInterrupt:
        print('\nThanks for using the script! Please raise any issues at: https://github.com/jcontini/fb-photo-downloader/issues/new')
        pass