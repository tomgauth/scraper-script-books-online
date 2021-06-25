from datetime import time
import time
from progress.bar import IncrementalBar
import progressbar

count=100

def clock():
  with IncrementalBar('Books scraped: ', max=count) as bar:
    for x in range(count):
      print(f'''{bar.next()} {x}''',end="\x08")
      time.sleep(0.5)
  bar.finish()



def lines():
  nlines = 2
  # scroll up to make room for output
  print(f"\033[{nlines}S", end="")

  # move cursor back up
  print(f"\033[{nlines}A", end="")

  # save current cursor position
  print("\033[s", end="")

  for t in range(10):
      # restore saved cursor position
      print("\033[u", end="")
      print(f"Line one @ {t}")
      print(f"Line two @ {t}")
      t += 1
      time.sleep(.5)

def w_txt():
  for i in progressbar.progressbar(range(100), end='', redirect_stdout=True):
      print('Some text', i)
      time.sleep(0.1)
