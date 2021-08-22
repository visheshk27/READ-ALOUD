esc = '\x1b'	# The escape character
csi = esc + '['	# Control Sequence Introducer, used for terminal control sequences
def sgr(n):	# Return a string that when printed will send a Select Graphic Rendition command to the terminal. n should be an integer indicating the display mode to select
	return(csi + str(n) + 'm')
def with_sgr(n, string):	# Return a string containing the given string with graphic rendition code n, and a code that resets the terminal after
	return(sgr(n)+string+sgr(0))

def justify_line(words, words_width, line_width):
	if not words:
		return ''
	if words[-1] and words[-1][-1] == '\n':
		return ' '.join(words)
	s = ''
	spaces = line_width - words_width	# The total n of spaces we need to add
	word_breaks = len(words)-1	# Number of word breaks in the line
	if(word_breaks > 0):
		base_spaces = spaces // word_breaks	# Number of spaces for each word break
		leftover_spaces = spaces % word_breaks	# Extra spaces left over when n of word breaks doesn't evenly divide number of spaces; we'll add an extra space to only the first however many word breaks
		for i in range(word_breaks):
			s += words[i]
			s += ' '*base_spaces
			if(i < leftover_spaces): s += ' '
	s += words[-1]
	s += '\n'
	return s

def find_page_with_word(word_n, index):
	for i in range(len(index)):
		if index[i] > word_n:
			return i
	return index[-1]

def split_words_into_pages(words, width, lines, min_width):
# This function takes an array of words, as is returned from split_text_into_words(), and splits them into pages of the specified width and height. The min_width argument is used in hyphenating words; if moving the next word to the next line would make the current line shorter than min_width, then that word will instead be broken up with a hyphen and split between the lines.
	word_n = 0
	pages = []
	word_index = []
	while word_n < len(words):
		page = justify_words(words, width, word_n, min_width, lines)
		pages.append(page[0])
		word_n = page[2]
		word_index.append(word_n)
	return (pages, word_index)

	
def split_text_into_words(text):
# This function splits a string of text into words. It will return an array of strings that each contain one word
	words = text.split(' ')
	i = 0
	while i < len(words):
		try:
			lineb = words[i].index('\n')
			words.insert(i+1, words[i][lineb+1:])
			words[i] = words[i][:lineb+1]
		except ValueError:
			pass
		i += 1
	return words



def justify_words(words, width, start_word = 0, min_width = 1, max_lines = None):
# This funciton goes through a list of words and assembles them into justified lines of the specified width
	out_text = ''
	total_width = 0
	this_line = []
	n_lines = 0
	i = start_word
	while i < len(words):
		word = words[i]
		if not word:	# A 'blank' word indicates multiple consective spaces in the input. Ignore.
			i += 1
			continue
		new_total_width = total_width + len(word)+1
		if new_total_width <= width:	# Adding this word to the line won't put it over the column width, so just add it
			this_line += [word]
			total_width = new_total_width
			if word[-1] == '\n':	# This is the last word in the paragraph so deal with that
				n_lines += 1
				out_text += justify_line(this_line, total_width-len(this_line), width)
				if max_lines and n_lines > max_lines-1:
					return (out_text, n_lines, i+1)
				total_width = 0
				this_line = []
		else:	# Adding this word would put it over the column width; start a new line 
			n_lines += 1
			if max_lines and n_lines > max_lines-1:
				out_text += justify_line(this_line, total_width-len(this_line), width)
				return (out_text, n_lines, i)
			if(total_width < (min_width or 1)):	# We need to break this word up with a hyphen
				firsthalf = word[:width-2-total_width]
				rest = word[width-2-total_width:]
				this_line += [firsthalf+'-']
				total_width = width
				#words.insert(i+1, rest)
				words[i] = rest
			i -= 1
			out_text += justify_line(this_line, total_width-len(this_line), width)
			total_width = 0
			this_line = []
		i+=1
	out_text += justify_line(this_line, total_width-len(this_line), width)
	return (out_text, n_lines, i)
