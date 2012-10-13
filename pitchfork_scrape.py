import csv
import urllib2
import re
from BeautifulSoup import BeautifulSoup
from rdio import Rdio
from rdio_consumer_credentials import *

#a method to check if a track is already in the csv array
def is_in_csv(csv_list, dictionary, key):
    for record in csv_list:
        if record[key] == dictionary[key]:
            return True
    return False

#takes in a track dictionary and looks for it in rdio, returns track key if found
def find_track(track):
    query = track['artist']+' '+track['title']
    search = rdio.call('search', { 'query' : query, 'types' : 'Track' })
    search = search['result']['results'] #gets rid of extraneous matter from search query return
    for result in search:
        if re.search(track['artist'],result['artist'],flags=re.IGNORECASE) != None:
            if re.search(track['title'],result['name'],flags=re.IGNORECASE) != None:
                if result['canStream']:
                    return result['key']

def add_to_playlist(key):
    rdio.call('addToPlaylist', { 'playlist' : PITCHFORK_PLAYLIST, 'tracks' : key })
    

#open pitchfork page and parse with beautiful soup
page = urllib2.urlopen("http://www.pitchfork.com/reviews/best/tracks/")
soup = BeautifulSoup(page)


# read csv rows into an array
csv_tracks = []
f = open('/home/barretts/pitchfork/tracks.csv', 'rb')
reader = csv.reader(f)
for row in reader:
    csv_tracks.append({'artist':row[1], 'title':row[0], 'status':row[2]})
f.close()

artist_list = []
title_list = []

#scrape all the artists
artists = soup.findAll("span", { "class" : "artist" })

for artist in artists:
    artist = artist.text
    artist = re.sub(r',','',artist)
    artist_list.append(artist.replace(":",""))

#scrape all the titles
titles = soup.findAll("span", { "class" : "title" })

for title in titles:
    title = title.text
    title = re.sub(r'\[.*\]\s*|,', '', title) #removes bracketed text (usually collaborators)
    title_list.append(title.replace("\"",""))

#combine the two
for i in range(0,len(artist_list)):
    new = {'artist':artist_list[i], 'title':title_list[i],'status':'0'}
    
    #check if combined tracks is already in csv & if not, add it
    if not is_in_csv(csv_tracks, new, 'title'):
        csv_tracks.append(new)
        print "Adding new track", new['title'], "to the CSV file"

#initiate rdio object
rdio = Rdio((RDIO_CONSUMER_KEY, RDIO_CONSUMER_SECRET), (RDIO_TOKEN, RDIO_TOKEN_SECRET))

#loop through any unadded tracks and see if they're on rdio, add 'em if they are
for track in csv_tracks:
    if track['status'] == '0':
        if find_track(track) != None:
            key = find_track(track)
            add_to_playlist(key)
            track['status'] = '1'
            print 'Adding %s by %s to the playlist' % (track['title'],track['artist'])
            
# write csv_tracks back out to file
f = open('/home/barretts/pitchfork/tracks.csv', 'w')
writer = csv.writer(f)
for record in csv_tracks:
    writer.writerow([record['title'],record['artist'],record['status']])
f.close()

