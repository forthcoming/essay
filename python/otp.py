import base64
import hashlib
import hmac
import os
import struct
import time


#  refer: https://github.com/google/google-authenticator-libpam/blob/master/src/google-authenticator.c#L49
class OnetimePassword:
    def __init__(self, digest_method=hashlib.sha1, length=6, interval=30):
        self.digest_method = digest_method
        self.__secret = base64.b32encode(os.urandom(10))
        self._length = length
        self._interval = interval

    @property
    def secret(self):
        return self.__secret

    def _totp(self, clock):
        counter = clock // self._interval  # used for getting different tokens, it is incremented with each use
        key = base64.b32decode(self.__secret)  # 10 bytes
        challenge = struct.pack('>Q', counter)  # unsigned long long,8bytes
        hmac_digest = hmac.new(key, challenge, self.digest_method).digest()
        offset = hmac_digest[-1] & 0b1111
        token_base = struct.unpack('>I', hmac_digest[offset:offset + 4])[0] & 0x7fffffff  # 舍弃最高位的符号位
        return token_base % (10 ** self._length)  # 如果长度不够6位,可以考虑填充前置0

    def totp(self):
        clock = int(time.time())
        return self._totp(clock)

    def valid_totp(self, token):
        if isinstance(token, int) and 0 <= token < 10 ** self._length:
            clock = int(time.time())
            return token == self._totp(clock)
        return False


if __name__ == '__main__':
    otp = OnetimePassword(interval=10)
    token = otp.totp()
    print(otp.secret, token)
    for _ in range(60):
        if not otp.valid_totp(token):
            token = otp.totp()
            print(time.monotonic(), token)
        time.sleep(1)
