import os
import sys

from cryptography.fernet import Fernet


def main():
    setting = sys.argv[1]
    fernet = Fernet(os.environ["MASTER_KEY"])
    print(fernet.decrypt(setting.encode("utf-8")))


if __name__ == "__main__":
    main()
