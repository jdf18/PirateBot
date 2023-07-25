from json import dumps, loads

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class EnvironmentContainer(metaclass=Singleton):
    def __init__(self, filename='.env', required=[]):
        try:
            # open the environment variables file (JSON format)
            with open(filename) as file:
                variables = loads(file.read())

            required = list(required)
            # instead of storing as a dictionary, store as attributes so they can be accessed using .s
            for key, value in variables.items():
                self.__setattr__(key, value)
                if key in required:
                    required.remove(key)
            # arguments passed in as required, if not found in the file, the program will ask for them to be entered manually
            # so that the rest of the program will not throw errors
            for key in required:
                self.__setattr__(key, input(f'Enter {key}: '))

        except FileNotFoundError:
            # file not found so get the user to enter all of the required values
            for key in required:
                value = input(f'Enter {key}: ')
                self.__setattr__(key, value)
        except Exception as e:
            raise e

class LangContatiner(metaclass=Singleton):
    class SubContainer:
        def __init__(self, data):
            self.data = data
        def exists(self, name):
            return bool(name in self.data)
        def update(self, dictionary):
            self.data.update(dictionary)
        def __getattr__(self, name):
            return self.data[name]
        def __getitem__(self, name):
            return self.data[name]

    def __init__(self, locale='en_GB'):
        # if the locale is not specified, get the locale from the system
        if not locale:
            import locale, ctypes
            locale = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()] + '.lang'

        # store data in the container and read the locale file
        self.locale = locale
        self.filename = locale + ".lang"
        self.data = {}
        try:
            with open(self.filename) as file:
                lines = file.readlines()
        except FileNotFoundError:
            pass
        except Exception as e:
            raise e

        # parse the file, creating SubContainer objects to store folders
        for i, line in enumerate(lines):
            if line.find('#') != -1:
                line = line[:line.index('#')]
            if line.strip() == '':
                continue

            key = line[:line.index('=')]
            value = line[line.index('=')+1:].rstrip().replace('\\n','\n')
            parts = key.split('.')
            
            current = self.data
            for j, part in enumerate(parts):
                try:
                    current = current[part]
                except:
                    needs_creating = parts[j:]
                    needs_creating.reverse()
                    curr = value
                    for p in needs_creating[:-1]:
                        curr = self.SubContainer({p:curr})
                    current.update({needs_creating[-1]: curr})
                    break

    def __getattr__(self, name):
        return self.data[name]