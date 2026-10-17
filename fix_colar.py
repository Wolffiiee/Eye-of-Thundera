import io

# Fix 1: Add colar method to Ponte class in app_web.py
fn = "D:/Projetos/PesquisaIA/app_web.py"
s = io.open(fn, encoding="utf-8").read()

# Find a good place to add the method - after janela_arrastar method
old = '''        except Exception as erro:
            p.registrar_erro("janela_arrastar", erro)
        return {}

    def definir_modo(self, modo):'''
new = '''        except Exception as erro:
            p.registrar_erro("janela_arrastar", erro)
        return {}

    def colar_texto(self):
        """Le o texto da area de transferencia do Windows (para o menu de contexto)."""
        try:
            import ctypes
            from ctypes import wintypes
            CF_UNICODETEXT = 13
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if not user32.OpenClipboard(None):
                return {"texto": "", "erro": "Nao foi possivel abrir a area de transferencia."}
            try:
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    return {"texto": "", "erro": "Nenhum texto na area de transferencia."}
                ptr = kernel32.GlobalLock(handle)
                if not ptr:
                    return {"texto": "", "erro": "Nao foi possivel ler a area de transferencia."}
                try:
                    texto = ctypes.wstring_at(ptr)
                finally:
                    kernel32.GlobalUnlock(handle)
                return {"texto": texto or ""}
            finally:
                user32.CloseClipboard()
        except Exception as erro:
            p.registrar_erro("colar_texto", erro)
            return {"texto": "", "erro": str(erro)}

    def definir_modo(self, modo):'''
assert old in s, "anchor not found"
s = s.replace(old, new, 1)
io.open(fn, "w", encoding="utf-8", newline="\n").write(s)
print("app_web.py: added colar_texto method")

# Fix 2: Update frontend colar function to use Python fallback
fn2 = "D:/Projetos/PesquisaIA/web/app.js"
s2 = io.open(fn2, encoding="utf-8").read()

old2 = '''async function colar(inicio, fim) {
  if (!navigator.clipboard || !navigator.clipboard.readText) {
    aviso("Para colar, use Ctrl+V.", true);
    return false;
  }
  try {
    const texto = await navigator.clipboard.readText();
    const campo = $("#entrada");
    campo.focus();
    campo.setRangeText(texto, inicio, fim, "end");
    ajustarAltura(); atualizarEnviar();
    return true;
  } catch (_e) {
    aviso("N\u00e3o consegui acessar a \u00e1rea de transfer\u00eancia. Use Ctrl+V.", true);
    return false
  }
}'''

new2 = '''async function colar(inicio, fim) {
  let texto = "";
  // Tenta a API do navegador primeiro.
  if (navigator.clipboard && navigator.clipboard.readText) {
    try {
      texto = await navigator.clipboard.readText();
    } catch (_e) { texto = ""; }
  }
  // Fallback: pede ao Python (Windows clipboard via ctypes).
  if (!texto) {
    try {
      const r = await chamar("colar_texto");
      if (r && r.texto) texto = r.texto;
      else if (r && r.erro) {
        aviso(r.erro + " Use Ctrl+V.", true);
        return false;
      }
    } catch (_e) {
      aviso("N\u00e3o consegui acessar a \u00e1rea de transfer\u00eancia. Use Ctrl+V.", true);
      return false;
    }
  }
  if (!texto) {
    aviso("N\u00e3o consegui acessar a \u00e1rea de transfer\u00eancia. Use Ctrl+V.", true);
    return false;
  }
  const campo = $("#entrada");
  campo.focus();
  campo.setRangeText(texto, inicio, fim, "end");
  ajustarAltura(); atualizarEnviar();
  return true;
}'''

assert old2 in s2, "colar function not found"
s2 = s2.replace(old2, new2, 1)
io.open(fn2, "w", encoding="utf-8", newline="\n").write(s2)
print("app.js: updated colar function with Python fallback")