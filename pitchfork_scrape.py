import csv
import urllib2
import re
from BeautifulSoup import BeautifulSoup
from rdio import Rdio
from rdio_consumer_credentials import *
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#checks if a track is already in the csv array
def is_in_csv(csv_list, dictionary, key):
    for record in csv_list:
        if record[key] == dictionary[key]:
            return True
    return False

#returns boolean true if a track is still available; key should be a string	
def is_available(key):
	track_info = rdio.call('get', {'keys' : key})
	availability = track_info['result'][key]['canStream']
	return availability

#puts last track of a playlist at start
def make_last_track_first(playlist_key):
	tracks_on_playlist = rdio.call('get', {'keys' : PITCHFORK_PLAYLIST_BETA, 'extras' : 'tracks'})
	tracks_on_playlist = tracks_on_playlist['result'][PITCHFORK_PLAYLIST_BETA]['tracks']
	
	track_keys = []
	
	for track in tracks_on_playlist:
		track_keys.append(track['key'])
		
	track_keys.insert(0, track_keys[-1])
	track_keys.pop()
	
	track_keys_string = ', '.join(track_keys)
	
	rdio.call('setPlaylistOrder', {'playlist': PITCHFORK_PLAYLIST_BETA, 'tracks' : track_keys_string})

# accepts dict with 'artist' and 'title'; searches rdio for matching track
# returns track key
def find_track(track_dict):
	query = track_dict['artist']+' '+track_dict['title']
	search = rdio.call('search', {'query': query, 'types': 'Track'})

	#set how many options to search amongst; never more than 5
	result_count = search['result']['track_count']
	choice_count = 5 if result_count > 5 else result_count #one-line if-else statement!

	choices = []

	for i in range(0, choice_count):
		choice_string = (search['result']['results'][i]['artist'] + ' ' + 
						 search['result']['results'][i]['name'])
		choices.append(choice_string)

	#use seatgeek fuzzywuzzy matching to find best choice
	best_choice = process.extractOne(query, choices)

	#weed out results with low similarity scores
	if (int(best_choice[1]))>89:

		index = choices.index(best_choice[0])

		#make sure it's streamable
		if search['result']['results'][index]['canStream']:

			#get the track key for the best choice
			key = search['result']['results'][index]['key']
			return key
			
def add_to_playlist(key):
    rdio.call('addToPlaylist', { 'playlist' : PITCHFORK_PLAYLIST_BETA, 'tracks' : key })
    
#open pitchfork page and parse with beautiful soup
page = urllib2.urlopen("http://www.pitchfork.com/reviews/best/tracks/")
soup = BeautifulSoup(page)

#path where history.csv is stored
history_file_path = ''

# read csv rows into an array
csv_tracks = []
f = open(history_file_path, 'rb')
reader = csv.reader(f)
for row in reader:
    csv_tracks.append({'artist':row[0], 'title':row[1], 'status':row[2], 'key':row[3]})
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
    new = {'artist':artist_list[i], 'title':title_list[i],'status':'0','key':''}
    
    #check if combined tracks is already in csv & if not, add it
    if not is_in_csv(csv_tracks, new, 'title'):
        csv_tracks.append(new)
        print "Adding new track", new['title'], "to the CSV file"

#initiate rdio object
rdio = Rdio((RDIO_CONSUMER_KEY, RDIO_CONSUMER_SECRET), (RDIO_TOKEN, RDIO_TOKEN_SECRET))

#loop through any unadded tracks and see if they're on rdio, add 'em if they are
for track in csv_tracks:
    
	#make sure track is still available, reset it to 0 if it's not
	if track['status'] == '1':
		availability = is_available(track['key'])
		if not availability:
			print "%s by %s is no longer available" % (track['title'], track['artist'])
			track['status'] = '0'

	if track['status'] == '0':
		if find_track(track) != None:
			key = find_track(track)
			add_to_playlist(key)
			make_last_track_first(PITCHFORK_PLAYLIST_BETA)
			track['status'] = '1'
			track['key'] = key #saves track key to csv as well 
			print 'Adding %s by %s to the playlist' % (track['title'],track['artist'])
            
# write csv_tracks back out to file
f = open(history_file_path, 'w')
writer = csv.writer(f)
for record in csv_tracks:
    writer.writerow([record['artist'],record['title'],record['status'],record['key']])
f.close()