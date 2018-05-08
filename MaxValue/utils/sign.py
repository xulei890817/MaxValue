import time
import sys
import json
import hashlib
import zlib
import base64


def okex_build_sign(secret_key, params):
    sign = ''
    my_params = params
    for key in sorted(my_params.keys()):
        sign += key + '=' + str(my_params[key]) + '&'
    return hashlib.md5((sign + 'secret_key=' + secret_key).encode("utf-8")).hexdigest().upper()
