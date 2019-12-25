import time
import requests
import datetime
import sys, getopt
from bs4 import BeautifulSoup
import re

def main(argv):
	length 									= 0
	time_out 								= False
	found_proxies							= []
	paste_list 								= set([])
	root_url 								= 'http://pastebin.com'
	raw_url 								= 'http://pastebin.com/raw/'
	start_time								= datetime.datetime.now()
	regex_proxie 							= '\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b:\\d{2,5}'
	main_proxy 								= ""
	file_name, keywords, append, run_time, match_total, crawl_total, main_proxy = initialize_options(argv)

	print(f"Crawling {root_url} Press ctrl+c to save file to {file_name}")

	try:
		# Continually loop until user stops execution
		while True:

			#	Get pastebin home page html
			root_html = BeautifulSoup(fetch_page(root_url, main_proxy), 'html.parser')
			
			#	For each paste in the public pastes section of home page
			for paste in find_new_pastes(root_html):
				
				#	look at length of paste_list prior to new element
				length = len(paste_list)
				paste_list.add(paste)

				#	If the length has increased the paste is unique since a set has no duplicate entries
				if len(paste_list) > length:
					
					#	Add the pastes url to found_proxies if it matches the regex
					raw_paste = raw_url+paste
					found_proxies = find_regex(raw_paste, found_proxies, regex_proxie, main_proxy)

				else:

					#	If keywords are not found enter time_out
					time_out = True

			# Enter the timeout 
			time.sleep(60)

			sys.stdout.write("\rCrawled total of %d Pastes, Keyword matches %d" % (len(paste_list), len(found_proxies)))
			sys.stdout.flush()

			if run_time and (start_time + datetime.timedelta(seconds=run_time)) < datetime.datetime.now():
				sys.stdout.write("\n\nReached time limit, Found %d matches." % len(found_proxies))
				write_out(found_proxies, append, file_name)
				sys.exit()

			# Exit if surpassed specified match timeout 
			if match_total and len(found_proxies) >= match_total:
				sys.stdout.write("\n\nReached match limit, Found %d matches." % len(found_proxies))
				write_out(found_proxies, append, file_name)
				sys.exit()

			# Exit if surpassed specified crawl total timeout 
			if crawl_total and len(paste_list) >= crawl_total:
				sys.stdout.write("\n\nReached total crawled Pastes limit, Found %d matches." % len(found_proxies))
				write_out(found_proxies, append, file_name)
				sys.exit()

	# 	On keyboard interupt
	except KeyboardInterrupt:
		write_out(found_proxies, append, file_name)

	#	If http request returns an error and 
	except requests.HTTPError as err:
		if err.code == 404:
			print("\n\nError 404: Pastes not found!")
		elif err.code == 403:
			print("\n\nError 403: Pastebin is mad at you!")
		else:
			print(f"\n\nYou\'re on your own on this one! Error code {err.code}")
		write_out(found_proxies, append, file_name)

	#	If http request returns an error and 
	except requests.URLRequired as err:
		print (f'\n\nYou\'re on your own on this one! Error code {err}')
		write_out(found_proxies, append, file_name)
	
	#	Proxy problem
	except requests.Timeout as err:
		print(f"Timeout")
		write_out(found_proxies, append, file_name)


def write_out(found_proxies, append, file_name):
	# 	if pastes with keywords have been found
	if len(found_proxies):

		#	Write or Append out urls of keyword pastes to file specified
		if append:
			f = open(file_name, 'a')
		else:
			f = open(file_name, 'w')

		for paste in found_proxies:
			f.write(paste + "\n")
		print("\n")
	else:
		print("\n\nNo relevant pastes found, exiting\n\n")

def find_new_pastes(root_html):
	new_pastes = []

	div = root_html.find('div', {'id': 'menu_2'})
	ul = div.find('ul', {'class': 'right_menu'})
	
	for li in ul.findChildren():
		if li.find('a'):
			new_pastes.append(str(li.find('a').get('href')).replace("/", ""))

	return new_pastes
	
def find_regex(raw_url, found_proxies, regex, proxy):
	found_proxies += re.findall(regex, fetch_page(raw_url, proxy))
	return found_proxies

def fetch_page(page, proxy):
	proxyDict = { 
				  "http"  : "http://" + proxy, 
				  "https" : "https://" + proxy, 
				  "ftp"   : "ftp://" + proxy
				}
	return requests.get(page, timeout = 30, proxies=proxyDict).text

def initialize_options(argv):
	keywords 			= ['ssh', 'pass', 'key', 'token']
	file_name 			= 'log.txt'
	append 				= False
	run_time 			= 0
	match_total			= None
	crawl_total	 		= None
	main_proxy			= "127.0.0.1"

	try:
		opts, args = getopt.getopt(argv,"h:k:o:t:n:m:a:p:")
	except getopt.GetoptError:
		print('pwnbin.py -k <keyword1>,<keyword2>,<keyword3>..... -o <outputfile>')
		sys.exit(2)

	for opt, arg in opts:

		if opt == '-h':
			print('pwnbin.py -k <keyword1>,<keyword2>,<keyword3>..... -o <outputfile>')
			sys.exit()
		elif opt == '-a':
			append = True
		elif opt == "-k":
			keywords = set(arg.split(","))
		elif opt == "-p":
			main_proxy = arg
		elif opt == "-o":
			file_name = arg
		elif opt == "-t":
			try:
				run_time = int(arg)
			except ValueError:
				print("Time must be an integer representation of seconds.")
				sys.exit()
		elif opt == '-m':
			try:
				match_total = int(arg)
			except ValueError:
				print("Number of matches must be an integer.")
				sys.exit()

		elif opt == '-n':
			try:
				crawl_total = int(arg)
			except ValueError:
				print("Number of total crawled pastes must be an integer.")
				sys.exit()

	return file_name, keywords, append, run_time, match_total, crawl_total, main_proxy

if __name__ == "__main__":
	main(sys.argv[1:])
