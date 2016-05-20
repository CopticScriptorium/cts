import re
import logging
from time import sleep
import resource
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from texts.models import HtmlVisualization

logger = logging.getLogger(__name__)


def collect(corpus, text, annis_server, driver):
	corpus_name = corpus.annis_corpus_name
	formats = corpus.html_visualization_formats.all()
	logger.info('Fetching %d visualizations' % len(formats))

	for html_format in formats:
		html_vis_url = annis_server.url_html_visualization(corpus_name, text.title, html_format.slug)

		try:
			logger.info(html_format.title)
			retries_left = 5
			connection_accepted = False
			while not connection_accepted and retries_left:
				try:
					driver.get(html_vis_url)
					connection_accepted = True
				except ConnectionRefusedError as cre:
					logger.warning(cre)
					driver.close()
					retries_left -= 1
					sleep(15)

			if retries_left == 0:
				raise VisServerRefusingConn()

			WebDriverWait(driver, 60 * 2).until(EC.presence_of_element_located((By.CLASS_NAME, "htmlvis")))
			driver.delete_all_cookies()

			body = driver.find_element_by_xpath("/html/body")
			text_html = body.get_attribute("innerHTML")
			styles = driver.find_elements_by_xpath("/html/head/style")
		except Exception as e:
			logger.error('Error getting %s: %s' % (html_vis_url, e))
			logger.error('Page source: ' + driver.page_source)
			text_html = ""
			styles = []

		if "Client response status: 403" in text_html:
			logger.error(" -- Error fetching " + html_vis_url)
			text_html = ""

		if text_html:
			# Add the styles
			for style_elem in styles:
				style_css = style_elem.get_attribute("innerHTML")
				text_html = text_html + "<style>" + style_css + "</style>"

			# For script element in the html, remove it
			script_elems = re.findall(r'<script.*script>', text_html, re.DOTALL)
			for script_elem in script_elems:
				text_html = text_html.replace( script_elem, "" )

		vis = HtmlVisualization()
		vis.visualization_format = html_format
		vis.html = text_html
		vis.save()

		text.html_visualizations.add(vis)

		self_max_mem, child_max_mem = [resource.getrusage(who).ru_maxrss for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)]
		logger.info('Max mem, self: {:,}, children: {:,}'.format(self_max_mem, child_max_mem))

class VisServerRefusingConn(Exception):
	pass
