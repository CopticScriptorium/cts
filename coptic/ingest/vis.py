import re
import os
import logging
from time import time, sleep
import resource
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from texts.models import HtmlVisualization

logger = logging.getLogger(__name__)
MAX_VIS_TRIES = 5


def collect(corpus, text, annis_server):
	corpus_name = corpus.annis_corpus_name
	formats = corpus.html_visualization_formats.all()
	logger.info('Fetching %d visualizations' % len(formats))
	driver = None

	for html_format in formats:
		html_vis_url = annis_server.url_html_visualization(corpus_name, text.title, html_format.slug)

		vis_tries_left = MAX_VIS_TRIES
		text_html = False

		while not text_html and vis_tries_left:
			try:
				if not driver:
					logger.debug("Starting browser")
					try:
						driver = webdriver.Chrome(os.environ.get('CHROMEDRIVER', '/usr/lib/chromium-browser/chromedriver'))
					except Exception as e:
						logger.error('Unable to start browser: %s' % e)
						return
					logger.debug(driver)

				logger.info(html_format.title)
				retries_left = 5
				connection_accepted = False
				vis_fetch_start_time = time()
				while not connection_accepted and retries_left:
					try:
						driver.get(html_vis_url)
						connection_accepted = True
					except ConnectionRefusedError as cre:
						logger.warning(cre)
						retries_left -= 1
						sleep(15)

				if retries_left == 0:
					raise VisServerRefusingConn()

				logger.info('Calling WebDriverWait')
				WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "htmlvis")))
				text_html = driver.find_element_by_xpath("/html/body").get_attribute("innerHTML")
				logger.info('WebDriverWait returned\t%s\t%s\t%s\t%d\t%d\t%f' % (
					corpus_name, text.title, html_format.slug, len(text_html),
					MAX_VIS_TRIES - vis_tries_left, time() - vis_fetch_start_time))
				driver.delete_all_cookies()

			except Exception as e:
				vis_tries_left -= 1
				logger.error('Error getting %s: %s' % (html_vis_url, e))
				logger.error('Page source: ' + driver.page_source)
				driver.quit()
				driver = None

		if not text_html:
			logger.error('Unable to get %s in %d tries.' % (html_vis_url, MAX_VIS_TRIES))
		else:
			# Add the styles
			for style_elem in driver.find_elements_by_xpath("/html/head/style"):
				text_html += "<style>" + style_elem.get_attribute("innerHTML") + "</style>"

			# Remove JavaScript elements
			for script_elem in re.findall(r'<script.*script>', text_html, re.DOTALL):
				text_html = text_html.replace(script_elem, "")

			vis = HtmlVisualization()
			vis.visualization_format = html_format
			vis.html = text_html
			vis.save()

			text.html_visualizations.add(vis)

		self_max_mem, child_max_mem = [resource.getrusage(who).ru_maxrss for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)]
		logger.info('Max mem, self: {:,}, children: {:,}'.format(self_max_mem, child_max_mem))

	if driver:
		driver.quit()

class VisServerRefusingConn(Exception):
	pass
