# !/usr/bin/env python
# -*-coding: utf-8 -*-
import hashlib


def md5(source: str):
    hashlib_md5 = hashlib.md5()
    hashlib_md5.update(source.encode(encoding='utf-8'))
    return hashlib_md5.hexdigest()
