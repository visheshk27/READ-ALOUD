#!/usr/bin/env python3

import curses
import argparse as ap
import re
import sys
from os import path

from libjust import *

try:
	import pyperclip
	paste = True
except ImportError:
	paste = False

try:
	import procname
	procname.setprocname('book')
except ImportError:
	pass

uparrows = [curses.KEY_UP, ord('k')]
downarrows = [curses.KEY_DOWN, ord('j')]
leftarrows = [curses.KEY_LEFT, ord('h')]
rightarrows = [curses.KEY_RIGHT, ord('l')]

nextpage = rightarrows + downarrows
prevpage = leftarrows + uparrows

par = ap.ArgumentParser(description = 'Terminal ebook reader')
par.add_argument('i', nargs='?', help = 'File to read from')
par.add_argument('-m', '--merge-lines', action = 'store_true', help = 'Merge lines separated by only a single newline', dest = 'm')
par.add_argument('-c', '--cols', type=int, default=2, help = 'Number of columns to display', dest = 'c')
par.add_argument('-p', '--clipboard', action = 'store_true', help = 'Get input from clipboard instead of file', dest = 'p')
par.add_argument('-v', '--verbose', action = 'store_true', help = 'Print extra info to the status line', dest = 'v')

args = par.parse_args()

re_linebreak = re.compile('(?<!\n)\n(?!\n)')
re_word = re.compile('[^ ]+')

global text

if args.p:
	if not paste:
		sys.stderr.write('Input from clipboard requires the pyperclip module\n')
		exit(1)
	text = pyperclip.paste()
	save = False
elif args.i is None or args.i == '-':
	infile = sys.stdin
	save = False
else:
	try:
		infilename = path.abspath(args.i)
		infile = open(args.i, 'r')
		savename = '%s/.%s.cbookmark'%(path.dirname(infilename),path.basename(infilename))
		save = True
		text = infile.read()
	except IOError as e:
		sys.stderr.write('Error: Could not open input file %s: %s\n'%(args.i, e.strerror))
		exit(1)


def create_column_layout(screen, cols, margin, top, bottom):
	(y, x) = screen.getmaxyx()
	page_wins = [None]*cols
	page_n_wins = [None]*cols
	page_width = (x-margin*(cols+1))//cols
	page_height = y-top-bottom
	page_n_width = page_width//2
	status_win = screen.derwin(1, x-2*margin, y-2, margin)
	for i in range(cols):
		page_wins[i] = screen.derwin(page_height, page_width, top, margin+i*(page_width+margin))
		page_n_wins[i] = screen.derwin(1, page_n_width, y-2, margin+i*(page_width+margin)+page_n_width)
	return page_wins, page_n_wins, status_win, page_width-1, page_height-1

def display_page(win, pages, page):
	(y, x) = win.getmaxyx()

def status(str, win):
	(y, x) = win.getmaxyx()
	win.addstr(0,0,str[:x-1])
	win.refresh()

def get_progress_bar(page, pages, win):
	(y, x) = win.getmaxyx()
	x -= 1
	done = int(page/pages*x)
	left = x-done
	return '*'*done+'-'*left

def ready_text(text, page_width, page_height):
	if args.m:
		text = re_linebreak.sub(' ', text)
	if text[-1] != '\n': text += '\n'
	words = split_text_into_words(text)
	return split_words_into_pages(words, page_width, page_height, 1)

def highlight_word(word, page_text, page_win):
	lines = page_text.split('\n')
	word_count = 0
	word_pos = None
	word_text = ''
	for l in range(len(lines)):
		words = re_word.findall(lines[l])
		new_word_count = word_count + len(words)+1
		if(new_word_count > word):
			word_match = words[word-word_count]
			word_text = word_match.group(0)
			word_pos = word_match.start(0)
			page_win.addstr(l, word_pos, word_text, curses.A_REVERSE)
			page_win.refresh()
			return
		else:
			word_count = new_word_count

def is_win_big_enough(y, x, cols, margin, top, bottom):
	page_width = (x-margin*(cols+1))//cols
	page_height = y-top-bottom
	return page_width > 7 and page_height > 0

margin = 3
top = 1
bottom = 2
def main(screen):
	global text
	curses.use_default_colors()
	curses.curs_set(False)
	screen.refresh()
	(y, x) = screen.getmaxyx()
	cols = args.c
	page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, margin, top, bottom)
	page = 0
	(pages, index) = ready_text(text, page_width, page_height)
	status_text = None
	if save:
		try:
			bkmkfile = open(savename, 'r')
			word_n = int(bkmkfile.read())
			page = find_page_with_word(word_n, index)
			page = (page//cols)*cols
		except Exception as e:
			pass
	word = index[page-1] if page > 0 else 0
	while True:
		screen.clear()
		for i in range(cols):
			if page+i < len(pages):
				if not curses.is_term_resized(y, x):
					page_wins[i].addstr(0,0,pages[page+i])
					if not status_text:
						page_n_wins[i].addstr(0,0,str(page+i+1))
					page_wins[i].refresh()
					page_n_wins[i].refresh()
				#highlight_word(1, pages[page+i], page_wins[i])
		if status_text:
			status(status_text, status_win)
			status_text = None
		k = screen.getch()
		if k == ord('q'):
			exit()
		elif k in nextpage:
			if page+cols < len(pages):
				page += cols
				word = index[page-1] if page > 0 else 0
		elif k in prevpage:
			if page >= cols:
				page -= cols
				word = index[page-1] if page > 0 else 0
		elif k == ord('=') or k == ord('+'):
			if is_win_big_enough(y, x, cols, margin, top, bottom):
				cols += 1
				page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, margin, top, bottom)
				(pages, index) = ready_text(text, page_width, page_height)
				page = find_page_with_word(word, index)
				page = (page//cols)*cols
			status_text = '%s column%s'%(cols,'' if cols == 1 else 's')
		elif k == ord('-') or k == ord('_'):
			if cols > 1:
				cols -= 1
				page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, margin, top, bottom)
				(pages, index) = ready_text(text, page_width, page_height)
				page = find_page_with_word(word, index)
				page = (page//cols)*cols
			status_text = '%s column%s'%(cols,'' if cols == 1 else 's')
		elif k == ord('S'):
			if save:
				try:
					bkmkfile = open(savename, 'w')
					if page == 0:
						bkmkfile.write('0')
					else:
						bkmkfile.write(str(word))
					status_text = 'Saved'
					bkmkfile.close()
				except IOError as e:
					status_text = '%s: %s'%(savename, e.strerror)
			else:
				status_text = 'Input not from file, save not available'
		elif k == ord('p'):
			status_text = get_progress_bar(page, len(pages), status_win)
			status(status_text, status_win)
			screen.getch()
			status_text = None
		elif k == ord('P') or k == 0x10:
			if not paste:
				status_text = 'Pasting from clipboard requires the pyperclip module'
			elif save:
				status_text = 'Input was from a file, cannot paste'
			else:
				pasted = pyperclip.paste()
				if not pasted:
					status_text = 'No text on clipboard'
				else:
					if k == 0x10:
						text = pasted
						status_text = 'Pasted (replacing)'
						page = 0
					else:
						text = text + ('\n\n' if args.m else '\n') + pasted
						status_text = 'Pasted (appending)'
					(pages, index) = ready_text(text, page_width, page_height)
		elif k == curses.KEY_RESIZE:
			oldpage = page
			page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, 3, 1, 2)
			(pages, index) = ready_text(text, page_width, page_height)
			page = find_page_with_word(word, index)
			page = (page//cols)*cols
			#t = "%s, %s (%s)"%(y, x, curses.is_term_resized(y,x))
			(y, x) = screen.getmaxyx()
			#status_text = "%s -> %s, %s (%s)"%(t, y, x, curses.is_term_resized(y,x))

		elif args.v:
			status_text = str(k)

curses.wrapper(main)
