<!-- i18n-source-sha256: b999ae6985930651e74b974b12109889360442811d6eeb306e6fa39754dbc173 -->
<div class="hero-shell" markdown>
<span class="hero-eyebrow">Plan de contrôle MCP compatible ChatGPT</span>

# local-shell-mcp

Donnez à votre assistant IA un shell contrôlé, un vrai workspace, Git, browser automation, file sharing et l’accès aux remote workers sans quitter le chat.

<div class="hero-actions" markdown>
[Commencer](getting-started/quickstart.md){ .hero-action .hero-action--primary }
[Choisir le runtime](guides/deployment.md){ .hero-action .hero-action--secondary }
[Référence des outils](reference/tools.md){ .hero-action .hero-action--secondary }
</div>
</div>

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### Environnement de code réel
Exécutez des tests, inspectez les repositories, appliquez des patches, utilisez Git et conservez un audit trail depuis un seul MCP endpoint.
</div>

<div class="feature-card" markdown>
### Couches runtime et client
Choisissez un runtime comme Docker, VS Code extension, binary, Python ou stdio, puis connectez séparément ChatGPT ou un autre MCP client.
</div>

<div class="feature-card" markdown>
### Contrôle des machines distantes
Connectez des machines derrière NAT, firewall ou HPC via des connexions worker sortantes sans ouvrir de ports SSH.
</div>
</div>

## Ce qui est fourni

`local-shell-mcp` expose un workspace local ou conteneurisé contrôlé à ChatGPT et aux autres clients MCP. Il fournit shell, shell persistant, filesystem, recherche, patch, Git, Playwright, audit, Sessions logiques durables avec Plans Goal optionnels, liens de fichiers tokenisés et outils remote worker via un serveur MCP compatible ChatGPT avec OAuth.

Utilisez-le lorsque l’IA doit inspecter un repository, exécuter des tests, modifier des fichiers, utiliser Git, collecter des browser evidence, produire des downloadable artifacts ou contrôler une machine distante ne pouvant se connecter qu’en sortie au control server.

## Architecture

```text
Couche runtime: Docker / VS Code extension / binary / Python / stdio
Couche exposition: localhost / HTTPS proxy / tunnel / stdio pipe
Couche client: ChatGPT / generic MCP client / editor helper
Workspace contrôlé: /workspace or configured workspace root
Remote workers optionnels: outbound machine connections
```

La limite d’isolation prévue est le container ou la VM qui exécute le service.

## Commencer selon le scénario

| Scénario | Commencer ici | Pourquoi |
|---|---|---|
| Premier deployment public ChatGPT | [Quickstart](getting-started/quickstart.md) | Parcours Docker Compose avec OAuth et configuration `/mcp` |
| Choisir la couche runtime | [Runtime choices](guides/deployment.md) | Explique Docker, VS Code, binary, Python et stdio comme options de runtime distinctes |
| Ajouter ChatGPT comme client | [ChatGPT connector](getting-started/chatgpt-connector.md) | Endpoint, OAuth, premier prompt sûr, tool discovery |
| Ajouter LSM à DeepSeek Harness | [Plugin DeepSeek Harness](clients/deepseek-harness.md) | Installer ce repository comme bundle DSH tout en conservant toute la surface d’outils LSM et remote workers |
| Exécuter depuis VS Code | [VS Code extension runtime](installation/vscode-extension.md) | Runtime lancé depuis l’éditeur et notes de sécurité host |
| Apprendre à utiliser le toolset | [Usage patterns](guides/usage-patterns.md) | Templates de prompt et guide de choix des tools |
| Comprendre chaque tool | [Tools reference](reference/tools.md) | Purpose, inputs, returns, combinations et notes de chaque tool |
| Connecter HPC, NPU/GPU ou server node | [Remote workers](guides/remote-workers.md) | Flux de join outbound worker et utilisation des tools distants |
| Partager des fichiers générés | [File links](guides/file-links.md) | URLs tokenisées avec TTL et révocation |
| Durcir le deployment | [Security](security.md) | Isolation, OAuth, portée workspace et audit logs |

## Principales familles de tools

| Famille | Exemples | Usage |
|---|---|---|
| Shell and Python | `run_shell`, `run_python`, `shell_start` | Builds, tests, scripts et processus longs |
| Files and search | `file_tree`, `file_grep`, `file_read`, `file_patch` | Inspection de repository et edits précis |
| Git | `run_shell`, `run_shell`, `run_shell`, `run_shell` | Workflows de contrôle de version révisables |
| Sessions et goals | `session_manage`, `plan_manage` | Handoff durable des tâches, rapports de progression et Goal mode optionnel |
| Browser | `browser_session`, `browser_snapshot`, `browser_act`, `browser_run_script` | Interaction persistante, checks UI, screenshots, docs rendus et texte de page |
| File links | `link_create`, `link_revoke` | Télécharger les artefacts générés depuis le chat |
| Remote workers | `remote_manage`, `run_shell`, `remote_transfer` | Machines derrière NAT, firewalls ou flux de connexion cluster |

## Workflows typiques

### Coder avec ChatGPT

1. Démarrez un runtime tel que Docker Compose, VS Code extension, binary ou Python dans un workspace dédié.
2. Exposez le runtime HTTP si ChatGPT a besoin d’un accès réseau.
3. Ajoutez l’endpoint public `/mcp` à ChatGPT.
4. Demandez d’abord d’inspecter le repository et d’exécuter des checks read-only.
5. Laissez ensuite patcher les fichiers, exécuter tests, revoir les diffs, commit et push après approbation.
6. Consultez l’audit log lorsque la tâche implique des file links ou systèmes distants.

### Host HPC ou accélérateur distant

1. Créez une invitation remote worker à usage unique.
2. Collez la commande générée sur le remote host.
3. Utilisez les tools normaux avec `machine`; Git via `run_shell` et les transferts via `remote_transfer`.
4. Révoquez le worker après la tâche.

### Génération d’artefacts

1. Laissez l’IA générer un file sous `/workspace`.
2. Créez un tokenized file link avec TTL/download limits.
3. Partagez le lien dans le chat.
4. Révoquez-le une fois terminé.

## Langue

Ce site est construit avec le plugin i18n natif de MkDocs. Utilisez le sélecteur de langue dans l’en-tête pour passer de English aux pages traduites. Les pages sans traduction utilisent English en fallback.
