import time
import requests
import datetime
import sys, getopt
from bs4 import BeautifulSoup
import re

def main(argv):
	length 									= 0
	found_proxies							= []
	paste_list 								= set([])
	root_url 								= 'http://pastebin.com'
	raw_url 								= 'http://pastebin.com/raw/'
	regex_proxie 							= '\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b:\\d{2,5}'
	main_proxy 								= ""
	file_name, append, timeout, main_proxy = initialize_options(argv)

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

			# Enter the timeout
			time_waited = 30
			sys.stdout.write("\rCrawled total of %d Pastes, Keyword matches %d, waiting %d seconds before next check." % (len(paste_list), len(found_proxies), time_waited))
			time.sleep(time_waited)
			sys.stdout.flush()

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
		print(f"\n\nTimeout")
		write_out(found_proxies, append, file_name)
	except requests.exceptions.ProxyError as err:
		print(f"\n\nProxyError")
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
	file_name 			= 'log.txt'
	append 				= False
	timeout 			= 0
	match_total			= None
	crawl_total	 		= None
	main_proxy			= "127.0.0.1"

	try:
		opts, args = getopt.getopt(argv,"h:o:t:p:a")
	except getopt.GetoptError:
		print('pwnbin.py -p <proxy:port> -o <outputfile> -t <timeout for requests> -a (append to file)')
		sys.exit(2)

	for opt, arg in opts:

		if opt == '-h':
			print('pwnbin.py -p <proxy:port> -o <outputfile> -t <timeout for requests> -a (append to file)')
			sys.exit()
		elif opt == '-a':
			append = True
		elif opt == "-p":
			main_proxy = arg
		elif opt == "-o":
			file_name = arg
		elif opt == "-t":
			try:
				timeout = int(arg)
			except ValueError:
				print("Time must be an integer representation of seconds.")
				sys.exit()

	return file_name, append, timeout, main_proxy

if __name__ == "__main__":
	main(sys.argv[1:])
