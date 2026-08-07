# Data Lifecycle Inventory

| Caminho/padrao | Tipo | Produtivo | Sensivel | Versionavel | Empacotavel | Backup | Retencao |
|---|---|---:|---:|---:|---:|---:|---|
| `data/database/acd.db` | banco real legado | sim | sim | nao | nao | sim | manter ate migracao segura |
| `%LOCALAPPDATA%\ACD\data\acd.db` | banco real oficial | sim | sim | nao | nao | sim | dados do usuario |
| `data/database/*.db` | banco de teste / legado | nao | possivel | nao | nao | sim | local apenas |
| `data/database/*.sqlite` | banco de teste / legado | nao | possivel | nao | nao | sim | local apenas |
| `data/database/*.sqlite3` | banco de teste / legado | nao | possivel | nao | nao | sim | local apenas |
| `*.db-wal`, `*.db-shm`, `*.db-journal`, `*.journal` | auxiliar SQLite | nao | sim | nao | nao | nao | temporario |
| `data/database/*.bak`, `backups/*.zip` | backup local | nao | sim | nao | nao | sim | evidencia local |
| `.env`, `.env.*` | configuracao | nao | sim | nao | nao | nao | local e secreta |
| `*.log`, `diagnostics*.json`, `support-diagnostics*.json` | log / diagnostico | nao | possivel | nao | nao | sim | local e curto prazo |
| `tests/fixtures/**` | fixture | nao | nao | sim | sim | sim | versionavel se sintatico |
| `attachments/**`, `curricula/**`, `candidate-documents/**` | anexo / documento pessoal | nao | sim | nao | nao | sim | local e revisado |

## Classificacao usada

- banco real
- banco de teste
- fixture
- demonstracao
- backup
- temporario
- cache
- configuracao
- anexo
- documento pessoal
- log
- desconhecido

## Evidencia atual

- Banco real conhecido: `data/database/acd.db`
- Backup local conhecido: `data/database/acd.pre-structured-resume-20260730T044516Z.bak`
- Backups adicionais rastreados: `data/database/acd_backup_before_refactor_20260701_203814.db`, `backups/acd-backup-20260730-072233.zip`, `backups/acd-backup-20260730-072453-clean.zip`
- `.env.example` existe; `.env` nao foi rastreado no inventario atual
- WAL/SHM nao foram encontrados no worktree atual
