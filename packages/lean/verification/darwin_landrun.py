#!/usr/bin/python3
"""Restricted macOS adapter for the pinned upstream Comparator argument subset."""

import sys
from boundary import landrun_main

if __name__ == "__main__":
    landrun_main(sys.argv[1:])
