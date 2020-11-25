import os
import glob

try:
    base_path = os.environ['ONSTREAM_HOME']
except KeyError:
    print('Could not get environment variable "base_path". This is needed for the tests!"')
    raise

Pictures = glob.glob(os.path.join(base_path, 'Pictures', '*'))
Duration = glob.glob(os.path.join(base_path, 'Duration', '*'))

for f in Pictures:
    os.remove(f)

for f in Duration:
    os.remove(f)
