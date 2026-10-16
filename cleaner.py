import io
p = "fix4.py"
d = io.open(p, encoding="utf-8").read()
d = d.rstrip()
q = chr(34)
while d.endswith(q):
    d = d[:-1].rstrip()
io.open(p, "w", encoding="utf-8").write(d + "\n")
print("ok")


def foo():
    return 'x'