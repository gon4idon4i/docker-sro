"""
PassKit — консольный набор инструментов для паролей.

Без аргументов открывает интерактивное меню, с аргументами работает как обычная утилита:
  passkit gen [-l ДЛИНА] [-n КОЛ-ВО] [--no-symbols]
  passkit phrase [-w СЛОВ]
  passkit check ПАРОЛЬ
  passkit hash ТЕКСТ [-a sha256|sha1|md5|sha512]
"""
import argparse
import getpass
import hashlib
import math
import secrets
import string
import sys

SYMBOLS = "!@#$%^&*()-_=+[]{}?"

# Слова для парольных фраз: латиница, чтобы фразу можно было ввести с любой раскладки
WORDS = (
    "alma tau dala ozen kol shana kun ai zhuldyz bulut "
    "zhel kar tas orman kustar at tuye qasqyr burkit qyran "
    "dombra kobyz kiiz ui shanyraq baursaq qymyz shubat "
    "saryarqa altai zhetisu oral ertis syrdariya ile balqash "
    "kitap qalam mektep dos bala ata ana zhol sapar baqyt"
).split()

COMMON = {"123456", "password", "qwerty", "111111", "12345678", "admin", "123123",
          "qwerty123", "1q2w3e4r", "iloveyou", "000000", "abc123", "password1"}

C = {"r": "\033[31m", "y": "\033[33m", "g": "\033[32m", "c": "\033[36m", "b": "\033[1m", "0": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def generate(length=16, symbols=True):
    pools = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    if symbols:
        pools.append(SYMBOLS)
    alphabet = "".join(pools)
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # гарантируем хотя бы один символ из каждой группы
        if length < len(pools) or all(any(ch in p for ch in pwd) for p in pools):
            return pwd


def passphrase(words=4):
    return "-".join(secrets.choice(WORDS) for _ in range(words)) + "-" + str(secrets.randbelow(100))


def entropy(pwd):
    pool = 0
    if any(c.islower() for c in pwd): pool += 26
    if any(c.isupper() for c in pwd): pool += 26
    if any(c.isdigit() for c in pwd): pool += 10
    if any(not c.isalnum() for c in pwd): pool += 33
    return len(pwd) * math.log2(pool) if pool else 0.0


def crack_time(bits):
    # 10 млрд попыток в секунду — порядок скорости офлайн-перебора на GPU
    seconds = 2 ** bits / 1e10 / 2
    for unit, size in (("лет", 31_536_000), ("дней", 86_400), ("часов", 3600), ("минут", 60)):
        if seconds >= size:
            value = seconds / size
            return f"{value:.1e} {unit}" if value > 1e6 else f"{value:.0f} {unit}"
    return "меньше минуты"


def check(pwd):
    bits = entropy(pwd)
    tips = []
    if pwd.lower() in COMMON:
        bits = 0
        tips.append("пароль есть в списке самых популярных")
    if len(pwd) < 12: tips.append("сделайте длину от 12 символов")
    if not any(c.isupper() for c in pwd): tips.append("добавьте заглавные буквы")
    if not any(c.isdigit() for c in pwd): tips.append("добавьте цифры")
    if all(c.isalnum() for c in pwd): tips.append("добавьте спецсимволы")
    if len(set(pwd)) < len(pwd) / 2: tips.append("слишком много повторов")

    if bits < 40: level, color = "СЛАБЫЙ", "r"
    elif bits < 70: level, color = "СРЕДНИЙ", "y"
    else: level, color = "НАДЁЖНЫЙ", "g"

    print(f"  Длина:     {len(pwd)}")
    print(f"  Энтропия:  {bits:.1f} бит")
    print(f"  Перебор:   ~{crack_time(bits)}")
    print(f"  Оценка:    {C[color]}{C['b']}{level}{C['0']}")
    for t in tips:
        print(f"   - {t}")


def do_hash(text, algo="sha256"):
    return hashlib.new(algo, text.encode()).hexdigest()


def menu():
    print(f"""{C['c']}{C['b']}
  ╔═══════════════════════════════╗
  ║   PassKit · пароли в Docker   ║
  ╚═══════════════════════════════╝{C['0']}""")
    while True:
        print(f"\n  {C['b']}1{C['0']} сгенерировать пароль   {C['b']}2{C['0']} парольная фраза")
        print(f"  {C['b']}3{C['0']} проверить пароль       {C['b']}4{C['0']} хэш строки")
        print(f"  {C['b']}0{C['0']} выход")
        try:
            choice = input("\n  > ").strip()
            if choice == "1":
                n = input("  Длина [16]: ").strip()
                length = int(n) if n.isdigit() and 4 <= int(n) <= 128 else 16
                for _ in range(3):
                    print("  " + C["g"] + generate(length) + C["0"])
            elif choice == "2":
                for _ in range(3):
                    print("  " + C["g"] + passphrase() + C["0"])
            elif choice == "3":
                pwd = getpass.getpass("  Пароль (ввод скрыт): ")
                if pwd:
                    check(pwd)
            elif choice == "4":
                text = input("  Текст: ")
                for algo in ("md5", "sha1", "sha256"):
                    print(f"  {algo:<7}{do_hash(text, algo)}")
            elif choice == "0":
                print("  Сау болыңыз!")
                return
        except (EOFError, KeyboardInterrupt):
            print()
            return


def main():
    if len(sys.argv) == 1:
        if not sys.stdin.isatty():
            print("Интерактивный режим требует флаг -it:  docker run --rm -it <образ>")
            print("Или используйте команды, см.:         docker run --rm <образ> --help")
            return
        return menu()

    p = argparse.ArgumentParser(prog="passkit", description="Генерация и проверка паролей")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen", help="случайные пароли")
    g.add_argument("-l", "--length", type=int, default=16)
    g.add_argument("-n", "--count", type=int, default=5)
    g.add_argument("--no-symbols", action="store_true")
    ph = sub.add_parser("phrase", help="парольная фраза из казахских слов")
    ph.add_argument("-w", "--words", type=int, default=4)
    c = sub.add_parser("check", help="оценить стойкость пароля")
    c.add_argument("password")
    h = sub.add_parser("hash", help="хэш строки")
    h.add_argument("text")
    h.add_argument("-a", "--algo", default="sha256", choices=["md5", "sha1", "sha256", "sha512"])
    a = p.parse_args()

    if a.cmd == "gen":
        for _ in range(max(1, a.count)):
            print(generate(max(4, a.length), not a.no_symbols))
    elif a.cmd == "phrase":
        print(passphrase(max(2, a.words)))
    elif a.cmd == "check":
        check(a.password)
    elif a.cmd == "hash":
        print(do_hash(a.text, a.algo))


if __name__ == "__main__":
    main()
