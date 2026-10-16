import io
s = io.open("web/app.js", encoding="utf-8").read()
print("geminiCard at top:", "const geminiCard = el" in s)
print("reposition fix:", "reajusta a posicao depois que as sugestoes" in s)
