import VersoManual
import Slean

open Verso.Genre Manual
open Verso.Genre.Manual.InlineLean

#doc (Manual) "Slean" =>
%%%
shortTitle := "Slean"
%%%

Une décision de recherche suit-elle les règles et les mesures consignées avant elle ? Slean aide la personne qui prépare ou relit un dossier à vérifier cette cohérence, puis à retrouver chaque élément de la décision.

Ici, un *dossier* est un fichier JSON contenant la question, le protocole figé, les observations, une décision et le journal des événements. L'exemple de ce manuel est entièrement inventé ; vous pouvez le comprendre sans installer Lean.

*Lire le résultat en une minute*

- *Règle fixée avant la mesure :* promouvoir seulement si `synthetic_delta` est strictement supérieur à `0.001 ratio`, avec un coût au plus égal à `10.00 cpu_s`.
- *Ce qui est consigné :* une observation de `0.002 ratio` et un coût de `2.50 cpu_s`.
- *Ce que Slean vérifie :* l'observation a la bonne métrique et la bonne unité, arrive après la règle et avant l'évaluation ; `0.002 > 0.001` et le coût reste sous le plafond.
- *Ce que le dossier annonce :* l'évaluation `pass`, puis la décision `promote`. Slean vérifie que cette chaîne est cohérente. Il ne prend pas la décision à la place de l'auteur.

Si l'unité de l'observation change, Slean signale `metric_unit` à `event-4`. Si la mesure manque, sa valeur est `null` et la décision est `defer` : une mesure absente n'est pas un zéro. Le [cas vérifié](commencer-par-un-cas-verifie/) montre les deux commandes utiles ; [lire la décision](lire-la-decision/) explique la chaîne et ses limites ; [les portes ET et OU](portes-et-ou/) ajoutent les liens consignés dans le schéma 0.3.

Slean vérifie le format, les références, l'ordre et les règles locales du dossier. Il ne réalise pas l'expérience, n'authentifie pas le capteur et ne prouve pas que la mesure est vraie.

Version de développement · schéma SLEANSCHEMAVERSIONTOKEN · Lean 4.28.0. Aucun tag n'est sélectionné pour ce build.

*Essayer sur une copie locale*

Si vous avez accès au dépôt et Lean installé, lancez depuis sa racine :

```
lake build
lake exe slean validate examples/valid.json
```

La seconde commande affiche exactement :

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

`ok: true` signifie que le dossier respecte les contrôles pris en charge. Ce résultat ne certifie ni les données d'origine ni la vérité de la conclusion.

# Commencer par un cas vérifié
%%%
file := "commencer-par-un-cas-verifie"
tag := "commencer-par-un-cas-verifie"
%%%

*Préparer la copie locale*

Il vous faut une copie autorisée de ce dépôt et `elan`, qui fournit Lean et Lake. Suivez les [instructions officielles d'installation de Lean](https://lean-lang.org/install/manual/) si ces outils ne sont pas installés. Le fichier `lean-toolchain` du dépôt sélectionne Lean 4.28.0. Cette prévisualisation n'est pas encore une installation publique anonyme.

Ouvrez un terminal à la racine du dépôt, là où se trouvent `lakefile.lean` et `examples/valid.json`, puis exécutez :

```
lake build
lake exe slean validate examples/valid.json
```

Résultat attendu de `validate` :

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

`events: 10` compte les entrées du journal complet, dont deux réservées au propriétaire. Cela ne représente ni dix expériences ni dix résultats confirmés.

*Lire le résultat plutôt que le seul « ok »*

Affichez la vue destinée à un agent :

```
lake exe slean view examples/valid.json agent
```

Dans le JSON renvoyé, repérez `observations[0]` (`status: "measured"`, `value: "0.002"`, `unit: "ratio"`) et `decisions[0]` (`result: "promote"`). La valeur reste une chaîne décimale pour éviter un arrondi implicite. L'événement qui fixe la règle est `event-1` ; l'observation est `event-4`, l'évaluation `event-6` et la décision `event-7`.

Vous avez ainsi répondu à une question précise : *la promotion annoncée suit-elle une observation antérieure conforme au protocole figé ?* Pour cet exemple synthétique, oui. Le chapitre suivant montre les liens et le calcul que Slean vérifie. La réussite de `validate` ne certifie pas le capteur, le fichier d'artefact ou la vérité de l'affirmation.

*Voir un refus concret*

Exécutez une copie de l'exemple dont l'unité de mesure a été modifiée :

```
lake exe slean validate examples/unit-mismatch.json
```

La commande sort avec un code non nul et affiche :

```
{"error":{"code":"metric_unit","event_id":"event-4","message":"observation metric or unit differs from frozen protocol","object_id":"observation-1"},"ok":false}
```

`event_id` situe l'échec dans le journal ; `metric_unit` indique que la métrique ou l'unité de l'observation ne correspond plus au protocole. Vous pouvez maintenant [lire la décision](lire-la-decision/) pour distinguer une erreur de dossier d'un résultat simplement inconnu.

# Lire la décision
%%%
file := "lire-la-decision"
tag := "lire-la-decision"
%%%

Le cas valide raconte une chaîne courte, dans cet ordre :

1. `event-1` fige le protocole : métrique `synthetic_delta`, unité `ratio`, seuil `0.001`, comparaison stricte, plafond de coût `10.00 cpu_s`.
2. `event-4` enregistre `0.002 ratio` pour la même métrique et le même essai.
3. `event-5` enregistre `2.50 cpu_s`, sous le plafond déclaré.
4. `event-6` cite l'observation et porte le verdict `pass` selon la règle locale `exact_v0`.
5. `event-7` cite cette évaluation et porte la décision `promote`.

Le seuil est strict parce que le protocole combine `direction: "gte"` et `inclusive: false` : `0.002 > 0.001`. Slean vérifie aussi que les références existent et que l'évaluation et la décision ne précèdent pas leurs éléments d'appui. `pass` est le verdict de l'évaluation ; `promote` est une décision distincte. Une dérogation humaine `override` exige une justification et ne devient pas un `pass`.

Vous pouvez figer la lecture au moment exact de la décision :

```
lake exe slean replay examples/valid.json 7
```

Ce rejeu ne prend que les sept premiers événements. Les événements `event-8` à `event-10` ne peuvent donc pas modifier rétroactivement le résultat de ce préfixe. La vue `agent` du chapitre précédent projette ensuite ce qui peut être montré à cette audience.

Un dossier peut être *valide mais indéterminé*. Comparez la vue de l'exemple sans mesure :

```
lake exe slean view examples/unknown.json agent
```

L'observation y a `status: "unknown"` et `value: null` ; la décision est `defer`. `null` veut dire « aucune mesure disponible », pas zéro. L'exemple `technical-error.json` conserve aussi une valeur nulle et une décision différée, avec un état d'erreur technique distinct.

La [lecture des portes ET et OU](portes-et-ou/) montre ensuite comment des dépendances consignées s'ajoutent au journal sans recalculer cette décision.

# Lire les portes ET et OU
%%%
file := "portes-et-ou"
tag := "portes-et-ou"
%%%

Une *porte de dépendance* décrit des liens ajoutés par l'auteur entre des éléments déjà enregistrés :

- `all_of` (ET) : tous les membres sont présentés comme prérequis de la cible.
- `any_of` (OU) : les membres sont présentés comme soutiens alternatifs.

Slean vérifie la forme, les identifiants, l'antériorité et la visibilité de ces liens. La porte ne calcule pas si les membres sont vrais, suffisants ou scientifiquement probants.

Depuis la racine du dépôt, validez le dossier synthétique au schéma `0.3.0` :

```
lake build
lake exe slean validate examples/dependency-gates.json
```

La seconde commande affiche exactement :

```
{"case_id":"synthetic-decision-1","events":13,"ok":true}
```

`ok: true` confirme ici que les deux portes sont des enregistrements recevables et que leurs références existent au bon moment ; ce n'est pas une évaluation de ET ou de OU. Dans ce dossier, `event-12` ajoute `gate-all-1` : `protocol-1` ET `assessment-1` sont des prérequis consignés pour `decision-1`. `event-13` ajoute `gate-any-1` : `observation-1` OU `observation-2` sont des soutiens alternatifs consignés pour `claim-1`. Ces événements arrivent après la décision `event-7` ; ils ne transforment pas rétroactivement son évaluation.

*Voir à quel moment chaque porte apparaît*

```
for n in 11 12 13; do
  lake exe slean replay examples/dependency-gates.json "$n" |
    python3 -c 'import json,sys; print(len(json.load(sys.stdin)["dependency_gates"]))'
done
```

Le résultat est exactement `0`, puis `1`, puis `2` sur trois lignes. Un *préfixe* est le nombre d'événements du début du journal pris en compte. Le préfixe 11 se termine avant les portes ; 12 inclut ET ; 13 inclut ET et OU. `lake exe slean view examples/dependency-gates.json agent` expose leurs opérateurs, membres et cibles dans `dependency_gates`.

Pour parcourir les mêmes préfixes dans l'Explorer local :

```
python3 explorer/render.py examples/dependency-gates.json --output explorer/_out/gates
python3 -m http.server 8768 --directory explorer/_out/gates
```

Ouvrez `http://127.0.0.1:8768/`, puis sélectionnez les événements 11, 12 et 13. La liste lisible au clavier, le détail de l'événement exact et la carte 2D proviennent du même journal validé. La carte répète les liens consignés ; elle ne démontre pas leur vérité.

*Ne pas confondre inconnu et zéro*

Comparez les deux vues `agent` :

```
lake exe slean view examples/dependency-gates-unknown.json agent
lake exe slean view examples/dependency-gates-zero.json agent
```

Dans le premier cas, la première observation a `status: "unknown"`, `value: null` et la décision antérieure est `defer` ; l'évaluation est `undetermined`. Dans le second, elle a `status: "measured"`, `value: "0"` et la décision est `reject` ; l'évaluation est `fail`. Les deux dossiers ont les mêmes portes ET/OU et une seconde observation positive enregistrée après la décision. La porte OU ne transforme donc ni l'absence de mesure en zéro, ni la décision passée en `promote`.

# Suivre la provenance
%%%
file := "suivre-la-provenance"
tag := "suivre-la-provenance"
%%%

La vue permet de remonter de la décision à l'évaluation, de l'évaluation à `observation-1`, puis de l'observation à `run-1` et `artifact-1`. Les identifiants sont des références vérifiées dans le dossier ; le simple texte d'une décision ne suffit pas. `event-8` ajoute un lien de soutien de l'observation vers `claim-1`, après le préfixe de décision.

La visibilité est appliquée *avant* le calcul de la vue. Sur le dossier synthétique, comparez :

```
lake exe slean view examples/valid.json agent
lake exe slean view examples/valid.json owner
```

La vue `agent` contient `observation-1` avec `0.002`, mais pas `private-observation-1`. La vue `owner` contient aussi cette seconde observation et sa valeur inventée `0.009`. Sur un vrai dossier, traitez la sortie `owner` comme privée ; ne l'envoyez pas à un agent ou à un site public. Vérifiez également le texte visible dans l'export `agent` avant de le partager.

Le schéma 0.2 permet de conserver des enregistrements source réservés au propriétaire. L'adaptateur borné vérifie notamment l'ordre des événements source, le gel initial, les liens entre prédictions et observations, la cohérence de l'achèvement avec le manifeste et la couverture de chaque observation. Il lit la trace en mémoire et ne sauvegarde pas le dossier privé. Python calcule les empreintes SHA-256 des artefacts source ; Lean vérifie les liens vers ces empreintes fournies, pas le calcul du hash ni le fonctionnement de l'évaluateur externe.

# Format et API
%%%
file := "format-et-api"
tag := "format-et-api"
%%%

*Choisir la commande selon la question*

- `validate <dossier.json>` : le dossier respecte-t-il les règles prises en charge ? La sortie contient `ok: true` ou une erreur avec `code`, `event_id` et `object_id` ; une erreur donne un code de sortie non nul.
- `replay <dossier.json> <N>` : quel était l'état après les `N` premiers événements ?
- `view <dossier.json> agent|owner` : quelles observations, décisions et relations sont visibles pour cette audience ?
- `export <dossier.json> agent|owner` : produire le dossier JSON canonique pour cette audience. Révisez le contenu avant partage.
- `timeline <dossier.json> agent|owner` : obtenir les états vérifiés de tous les préfixes visibles, utilisés par l'Explorer local.
- `proof <dossier.json>` et `proof-statement` : examiner les statuts formels locaux et l'unique énoncé de théorème fixé par le projet.

Les commandes qui lisent un dossier acceptent aussi `-` comme chemin d'entrée standard. Par exemple, depuis la racine du dépôt :

```
lake exe slean view examples/valid.json agent
```

`examples/valid.json` est au schéma `0.1.0`. Le schéma `0.2.0` ajoute les enregistrements source réservés au propriétaire ; `0.3.0` ajoute `dependency_gate_recorded` avec `all_of` ou `any_of`. Dans chaque dossier, `schema_version` et `semantics_version` doivent former une paire prise en charge ; Slean ne migre pas un dossier implicitement. Consultez `schema/v0.1.0.schema.json`, `schema/v0.2.0.schema.json` et `schema/v0.3.0.schema.json` dans le dépôt pour les champs exacts. Les nombres décimaux exacts, comme `"0.002"`, sont des chaînes ; `null` reste distinct de `"0"`.

*Si vous écrivez du Lean*

L'API typée permet de construire le même type de dossier. Ces déclarations sont vérifiées lors de la compilation de ce manuel :

```lean
#check Slean.CaseFile
#check Slean.replay
#check Slean.assessExact
#check Slean.project
#check Slean.DependencyGate
```

`examples/Synthetic.lean` contient le cas typé complet. `bash tests/check.sh` le compile et compare son export `agent` avec la fixture JSON, octet par octet. Un statut de preuve importé depuis JSON n'accorde jamais `kernel_checked` ; ce statut est réservé à la déclaration locale fixée et contrôlée par le noyau Lean.

# Limites et état du développement
%%%
file := "limites-et-etat-du-developpement"
tag := "limites-et-etat-du-developpement"
%%%

*Slean vérifie ici :* la forme versionnée du dossier, les identifiants et références, l'ordre causal du journal, la comparaison décimale locale, le plafond de coût déclaré, la règle de promotion, les références des portes ET/OU et la projection d'audience. Il peut montrer une erreur précise ou conserver un résultat indéterminé.

*Slean ne vérifie pas ici :* que la mesure a été réellement prise, que les octets d'un artefact sont authentiques, que l'horloge externe ou l'évaluateur est fiable, qu'une porte ET/OU démontre sa cible, que la décision humaine est judicieuse, ou que l'affirmation scientifique est vraie. Le théorème Lean local porte sur une propriété conditionnelle du mécanisme, pas sur ces faits empiriques. Aucune vérification indépendante de preuve n'est configurée.

Ce site est un prototype local antérieur à la publication. Les exemples sont synthétiques. La licence publique, la visibilité du dépôt, le domaine et les intégrations restent des décisions distinctes. La construction exécute les tests et compile les exemples avant de générer le manuel. `build-info.json` indique le commit source, la propreté de l'arbre, le schéma, Lean et le tag sélectionné ; un build sans tag reste une prévisualisation de développement.
