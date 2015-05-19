# -*- coding: utf-8 -*-
from logging import *
import config


if config.config["DEBUG"] is True:
    basicConfig(level=10, format="%(levelname)s - %(message)s")
elif config.config["DEBUG"] is False:
    basicConfig(filename="db/logging.log", level=10, format="%(asctime)s : %(levelname)s : %(message)s")
