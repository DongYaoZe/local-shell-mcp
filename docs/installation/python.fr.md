<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Runtimes Python, pipx et source

Les runtimes Python sont utiles pour le développement, le débogage et les environnements où la gestion de paquets Python est plus simple que Docker. Ils exécutent le même serveur que les runtimes Docker et binary.

Utilisez cette page pour trois cas liés :

- `pipx install local-shell-mcp` : installation d’un executable au niveau utilisateur.
- `pip install local-shell-mcp` : installation dans un virtual environment existant.
- Editable source checkout : développer ou déboguer le projet lui-même.

## Installation pipx

`pipx` est l’installation Python la plus propre pour les utilisateurs ordinaires, car il attribue au command son propre virtual environment tout en exposant un executable dans `PATH`.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

Démarrez un serveur MCP HTTP local :

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

Vérifiez l’état :

```bash
curl -i http://127.0.0.1:8765/healthz
```

## Installation en virtual environment

Utilisez cette méthode si vous gérez déjà manuellement vos environnements Python :

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

Le process utilise les outils installés sur l’hôte. Le paquet Python n’installe pas à votre place les compilateurs, Git, les dépendances système du navigateur ni les dépendances du projet.

## Editable source checkout

Utilisez ceci pour développer le projet :

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

Exécutez les contrôles :

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## Configuration du navigateur

Le paquet Python dépend de Playwright, mais les browser binaries peuvent encore devoir être installés sur l’hôte :

```bash
python -m playwright install chromium
```

Certains hôtes Linux nécessitent des dépendances navigateur supplémentaires. Docker évite la majeure partie de ce travail car l’image part d’une Playwright base image.

## Utilisation publique HTTP MCP

Pour ChatGPT ou un autre public HTTP MCP client, configurez le même public origin et OAuth que pour les autres runtimes HTTP, puis exposez le port local via un reverse proxy ou tunnel.

L’endpoint MCP public est :

```text
https://your-public-host.example.com/mcp
```

## Modes de développement

| Mode | Command | Usage |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | MCP clients complets via HTTP, y compris ChatGPT derrière HTTPS |
| REST-style HTTP | `local-shell-mcp --mode http` | Endpoints de diagnostic ou compatibilité, pas la route principale de ChatGPT |
| stdio | `local-shell-mcp --mode stdio` | MCP clients locaux qui lancent le process |

`mode=both` est réservé et ne doit actuellement pas être utilisé comme mode d’un seul process.

## Sécurité du host runtime

Les installations Python s’exécutent sous votre utilisateur hôte, sauf si elles sont placées dans une VM ou un container. Gardez un workspace limité, laissez full-container mode désactivé et ne pointez pas le workspace vers un home directory.

Utilisez Docker Compose pour les repositories non fiables, les tâches fortement dépendantes des package managers ou les workflows où la réinitialisation importe davantage que l’intégration à l’hôte.
