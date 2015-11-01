import re
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from texts.models import HtmlVisualization

logger = logging.getLogger(__name__)


def collect(corpus, text, annis_server, driver):

	for html_format in corpus.html_visualization_formats.all():
		corpora_url = annis_server.base_domain + annis_server.html_visualization_url.replace(
			":corpus_name", corpus.annis_corpus_name).replace(":document_name", text.title).replace(
			":html_visualization_format", html_format.slug)

		try:
			logger.info('Fetching from ' + corpora_url)
			driver.get(corpora_url)
			WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "htmlvis")))
			driver.delete_all_cookies()

			body = driver.find_element_by_xpath("/html/body")
			text_html = body.get_attribute("innerHTML")
			styles = driver.find_elements_by_xpath("/html/head/style")
		except:
			text_html = ""
			styles = []
			driver.quit()
			driver = webdriver.Firefox()

		if "Client response status: 403" in text_html:
			logger.error(" -- Error fetching " + corpora_url)
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
