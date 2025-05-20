import asyncio
import aiohttp as aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pprint


BASE_URL = 'https://en.wikipedia.org'


async def fetch(url):
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
      return await resp.text()


async def crawl():
  pages = []

  content = await fetch(urljoin(BASE_URL, '/wiki/List_of_programming_languages'))
  soup = BeautifulSoup(content, 'html.parser')
  for link in soup.select('div.div-col a'):
    pages.append(urljoin(BASE_URL, link['href']))

  return pages


async def scrape(link):
  content = await fetch(link)
  soup = BeautifulSoup(content, 'html.parser')

  # Select name
  name = soup.select_one('caption.infobox-title')

  if name is not None:
    name = name.text

    creator = soup.select_one('table.infobox tr:has(th a:-soup-contains("Developer", "Designed by")) td')
    if creator is not None:
      creator = creator.text

    return [name, creator]

  return []


async def main():
  links = await crawl()

  tasks = []
  for link in links:
    tasks.append(scrape(link))
  authors = await asyncio.gather(*tasks)

  pp = pprint.PrettyPrinter()
  pp.pprint(authors)


asyncio.run(main())