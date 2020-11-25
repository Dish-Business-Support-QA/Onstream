import os
import shutil
from Chrome_Thread import mc
from OnStream_Chrome import testrun

try:
    base_path = os.environ['ONSTREAM_HOME']
except KeyError:
    print('Could not get environment variable "base_path". This is needed for the tests!"')
    raise


Archived = os.path.join(base_path) + '/' + 'Archived' + '/' + testrun + '/' + mc.get_value()

os.mkdir(Archived)

Pictures = os.path.join(base_path) + '/' + 'Pictures' + '/'
Duration = os.path.join(base_path) + '/' + 'Duration' + '/'

dest = os.path.join(base_path, 'Archived') + '/' + testrun + '/' + mc.get_value()

try:
    PicturesFile = os.listdir(Pictures)
    for f in PicturesFile:
        if not f.startswith('.'):
            shutil.move(Pictures+f, dest)
except FileNotFoundError:
    print("File Not Found at " + Pictures)
    pass

try:
    DurationFile = os.listdir(Duration)
    for f in DurationFile:
        if not f.startswith('.'):
            shutil.move(Duration+f, dest)
except FileNotFoundError:
    print("File Not Found at " + Duration)
    pass
