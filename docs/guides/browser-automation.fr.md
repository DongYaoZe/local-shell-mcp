<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Automatisation du navigateur

Les outils de navigateur utilisent Playwright pour inspecter les pages, capturer des preuves et exécuter des workflows de navigateur reproductibles. La tool surface publique est volontairement réduite.

## Outils

| Tool | Rôle |
|---|---|
| `browser_session` | Démarrer, lister, fermer ou nettoyer des sessions de navigateur persistantes ; réutiliser facultativement un profile ou un storage state. |
| `browser_snapshot` | Lire un texte de page borné, les erreurs page/network et les éléments interactifs avec des refs courtes comme `e1` ; capturer facultativement une screenshot. |
| `browser_act` | Exécuter des actions structurées navigation, click, fill, select, key, wait et multipages à partir de refs de snapshot ou de CSS selectors. |
| `browser_run_script` | Exécuter un script Python Playwright complet lorsque les actions de haut niveau ne suffisent pas. |

Tous les outils de navigateur acceptent un `machine` facultatif. Les dépendances du navigateur doivent déjà être installées sur le controller ou worker sélectionné ; l’installation se fait avec des commandes shell ordinaires telles que `python -m playwright install chromium`.

## Flux courants

Pour un travail interactif, appelez `browser_session(action="start", url=...)`, puis `browser_snapshot`. Le snapshot renvoie des références courtes telles que `e1` et `e2` ; transmettez-les directement à `browser_act`, par exemple `{"action": "click", "target": "e1"}` ou `{"action": "fill", "target": "e2", "value": "..."}`. Reprenez un snapshot après navigation, car les refs d’éléments représentent l’état de la page et ne sont pas des selectors permanents.

Pour l’inspection ordinaire et les screenshots, préférez `browser_session` avec `browser_snapshot` ; le snapshot peut renvoyer un texte visible borné et enregistrer une screenshot. Utilisez `browser_run_script` pour l’évaluation JavaScript, la logique personnalisée de capture/PDF ou les interactions non représentées par `browser_act`.

Gardez les scripts bornés, définissez des timeouts explicites, enregistrez les artifacts dans le workspace et évitez de saisir des credentials sauf si l’environnement est dédié à la tâche.
