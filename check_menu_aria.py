import io
s = io.open('web/app.js', encoding='utf-8').read()
idx = s.find('menu.setAttribute("aria-label"')
print(s[idx-50:idx+100])