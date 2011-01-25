from urllib import quote_plus, unquote_plus

def paginate(self, q, offset, per_page, search_info):
	" Return an html pagination for the search results. "

	if search_info.totalfound == 0:
		return ''

	MAX_PAGES = 10

	path = self.request.path_url
	html = []

	q = quote_plus(q)

	if offset > 0:
		html.append('<a href="%s?q=%s&offset=%d">&lt; Prev</a>' % (path, q, offset-per_page))

	page_offset = 0
	pages = search_info.totalfound / per_page + 1
	current_page = offset/per_page + 1

	if (current_page > MAX_PAGES/2) and ( (MAX_PAGES/2+current_page) < pages):
		page_offset = current_page - MAX_PAGES/2

	for n in range(1+page_offset, min(MAX_PAGES+1+page_offset, pages) ):
		if n==current_page:
			html.append('<b>%d</b>' % n)
		else:
			html.append('<a href="%s?q=%s&offset=%d">%d</a>' % (
				path, q, (n-1)*per_page, n))

	if pages > (current_page+1):
		html.append('<a href="%s?q=%s&offset=%d">Next &gt;</a>' % (
			path, q, current_page*per_page))

		return u' | '.join(html)
