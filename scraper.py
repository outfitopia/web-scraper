import requests, os
import multiprocessing
from PIL import Image
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup

class VogueGallery(object):
  def __init__(self, url):
    self.base_url = 'https://vogue.co.uk'
    self.page = requests.get(url).content
    self.designers = []
  
  def populate_shows(self):
    shows = BeautifulSoup(self.page).findAll('li', 'directoryListItem')
    show_urls = map(
      lambda tag: 
        {
          'image': tag['data-directoryimageurl'], 
          'collection': self.base_url+tag['data-showurl']
        },
      shows) 
    for data in show_urls:
      try:
        show = Show(data['image'], data['collection'])
        self.designers.append(show)
      except Exception as e:
        print (e)


class ImageURLParser(object):
  def __init__(self, url):
    vals = url.split('/')[5:]
    self.season = vals[0][:2]
    self.year = vals[0][2:]
    self.city = vals[1]
    self.collection_type = vals[2]
    self.store_name = vals[3]

class Show(object):
  def __init__(self, image_url, collection_url):
    parsedURL = ImageURLParser(image_url)
    self.name = self._toHumanName(parsedURL.store_name)
    self.store_name = parsedURL.store_name
    self.season = parsedURL.season
    self.show_type = parsedURL.collection_type
    self.year = int(parsedURL.year)
    self.city = parsedURL.city
    
    self.base_url = collection_url
    self.image_count = None  

  @property
  def images_url(self):
    return ("http://cdni.condenast.co.uk/1280x1920/Shows/"
      "%(season)s%(year)d/%(city)s/%(show_type)s/%(designer)s/" % ({
        'season': self.season,
        'year': self.year,
        'city': self.city,
        'show_type': self.show_type,
        'designer': self.store_name
      }))

  def get_image_count(self):
    def parse_total(page):
      sentence = page.find(id="SlideNumbering").contents[0].strip()
      if sentence:
        total = int(sentence.split(' of ')[-1])
      if total:
        return total
      return None
    
    page = requests.get(self.base_url+'/image/1').content
    soup = BeautifulSoup(page)
    self.image_count = parse_total(soup)
    return True
  
  def download_show(self):
    designer = self.store_name
    season = self.season
    show_type = self.show_type
    year = self.year
    city = self.city
    
    def prepare_path(designer, season, show_type, year):
      designer = self.name
      return "%(designer)s/%(show_type)s/%(season)s%(year)d/" % locals()
    
    path = prepare_path(designer, season, show_type, year)
    print (path)

    for i in xrange(10, 2000000, 10):
      img = str(i).zfill(5)  
      name = str(i/10)+'.jpg'
      url = "%s%s" % (self.images_url, ("%sbig.jpg" % img))


      if not os.path.exists(path):
        os.makedirs(path)
      if not os.path.exists(path+name):
        r = requests.get(url)
        if not (r.status_code >= 200 and r.status_code <= 301):
          print ("Failed to fetch %s " % self)
          break
        try:
          im = Image.open(StringIO(r.content))
          im.save(path+name, 'JPEG')
        except IOError as e:
          print ("Failed to write out " + path+name)

    return True

  def __call__(self):
    self.download_show()
  def _toHumanName(self, name):
    return name.replace('_', ' ')     
  def __repr__(self):
    return "%s %s %s%s" % (self.name, self.show_type, self.season, self.year)

if __name__ == '__main__':
  #FIXME: ArgV
  ss2013 = VogueGallery('https://www.vogue.co.uk/article/doja-cat-favourite-headwear-artist-kazclops')
  ss2013.populate_shows()
  
  res = []
  pool = multiprocessing.Pool(processes=8)
  for designer in ss2013.designers:
    res.append(pool.apply_async(designer)) 
  [r.get() for r in res]