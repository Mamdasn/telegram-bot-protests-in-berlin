import os
from configparser import ConfigParser


def config(section="postgresql"):
    file_path = os.path.abspath(__file__)
    parent_path = os.path.dirname(file_path)
    filename = os.path.join(parent_path, "database.ini")

    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    return db
