# Ambiente Windows

O ACD deve ser executado pela virtual environment do projeto, nunca pelo Python global.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints/windows-py314.txt -e .
.\.venv\Scripts\acd.exe
```

Para desenvolvimento e testes:

```powershell
.\.venv\Scripts\python.exe -m pip install -c constraints/windows-py314.txt -e ".[dev]"
```

`pyproject.toml` é a fonte oficial. `requirements.txt` existe somente como
compatibilidade e delega para a instalação editável do projeto.

Alternativamente, use `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_app.ps1`.

As versões validadas no alvo Windows/Python 3.14 estão em
`constraints/windows-py314.txt`. SDK ausente é instalação incompleta;
credenciais ausentes apenas selecionam o provider não configurado.
