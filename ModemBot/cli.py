#!/usr/bin/env python3

import os
import modem

if __name__ == "__main__":
    # TODO: Load config.toml, call getCPE() to get the modem instance
    m = modem.ZTEh1600("192.168.1.1", "admin", os.getenv("PASSWORD"))

    m.connect()
    m.updateStats()
    m.showStats()
    m.disconnect()
