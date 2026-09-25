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

Si l'unité de l'observation change, Slean signale `metric_unit` à `event-4`. Si la mesure manque, sa valeur est `null` et la décision est `defer` : une mesure absente n'est pas un zéro. Le [cas vérifié](commencer-par-un-cas-verifie/) montre les deux commandes utiles ; [lire la décision](lire-la-decision/) explique la chaîne et ses limites ; [les portes ET et OU](portes-et-ou/) ajoutent les liens consignés dans le schéma 0.3. Les [exemples exécutables](exemples-lean/) montrent l'API typée et un cas rétrospectif sur des données publiques.

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

Ouvrez un terminal à la racine du dépôt, là où se trouvent `lakefile.toml` et `examples/valid.json`, puis exécutez :

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

Le plafond de `10.00 cpu_s` concerne ce protocole figé pour l'ensemble de ses essais. Chaque montant enregistré en `cpu_s` compte, même si sa couverture est partielle. Un second essai qui ajoute `7.51 cpu_s` après les `2.50 cpu_s` du premier est refusé avec `cost_cap_exceeded` ; une autre unité de coût reste enregistrée sans conversion.

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
- `export <dossier.json> agent|owner` : produire une enveloppe versionnée avec le dossier canonique et la version de Lean. Révisez le contenu avant partage. Utilisez `export-case` seulement si un consommateur attend l'ancien dossier brut.
- `timeline <dossier.json> agent|owner` : obtenir les états vérifiés de tous les préfixes visibles, utilisés par l'Explorer local.
- `proof <dossier.json>` et `proof-statement` : examiner les déclarations, leur admissibilité locale à l'attestation, les dépendances du projet et l'unique énoncé de théorème fixé par le projet. Sur un commit propre, `python3 tools/attest_proof.py examples/formal-claim.json` n'émet `kernel_checked` qu'avec les empreintes du build exact et de l'export filtré pour son public. Lake, le CLI et ce script Python restent dans la chaîne de confiance ; il ne s'agit pas d'une revérification indépendante.

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

`examples/Synthetic.lean` contient le cas typé complet. `bash tests/check.sh` le compile et compare ses octets à la projection `export-case agent` de la fixture JSON. Un statut de preuve importé depuis JSON n'accorde jamais `kernel_checked` ; le CLI conserve aussi une déclaration locale concordante à `declared` jusqu'à ce que l'attestation sur un build propre relie son reçu aux artefacts exacts.

# Exemples exécutables
%%%
file := "exemples-lean"
tag := "exemples-lean"
%%%

Les quatre premiers exemples sont des fichiers Lean 4 complets qui appellent l'API typée actuelle de Slean. Slean n'a pas de parseur de langage source distinct : le CLI lit des dossiers JSON ou des enveloppes d'export versionnées, tandis que `lake env lean --run` exécute ces fichiers Lean. Placez-vous à la racine du dépôt, utilisez Lean 4.28.0 fixé par `lean-toolchain`, puis lancez `lake build` une fois. Leurs entrées et leurs valeurs sont synthétiques. Le cinquième exemple utilise un jeu de données public réel et un protocole pédagogique rédigé séparément.

*1. Consigner et rejouer un dossier de décision*

Problème : consigner une règle figée, un essai, une référence d'artefact, une mesure, un coût, une évaluation et une décision, puis examiner ce qui existait au moment de la décision. La source typée ci-dessous produit la projection `agent` de la fixture vérifiée `examples/valid.json`.

*Source complète : `examples/Synthetic.lean`*

```
import Slean

open Lean Slean

private def ident (id : String) : Identity :=
  { id, version := 1, domain := "synthetic-computation",
    provenance := "synthetic://slean-v0", audience := "agent" }

private def protocol : FrozenProtocol :=
  { identity := ident "protocol-1", claim_ref := "claim-1",
    metric_id := "synthetic_delta", unit := "ratio", direction := "gte",
    threshold := "0.001", inclusive := false, data_scope := "synthetic input A",
    evaluator_ref := "synthetic-evaluator-v1", cost_cap := "10.00",
    cost_unit := "cpu_s", stop_rule := "one synthetic measurement",
    frozen_at := "2026-01-01T00:01:00Z" }

private def run : Run :=
  { identity := ident "run-1", protocol_ref := "protocol-1",
    input_ref := "synthetic-input-A", seed := "7" }

private def artifact : ArtifactRef :=
  { identity := ident "artifact-1", digest := "sha256:" ++ String.ofList (List.replicate 64 'a'),
    media_type := "application/json" }

private def observation : Observation :=
  { identity := ident "observation-1", run_ref := "run-1",
    metric_id := "synthetic_delta", unit := "ratio", value := some "0.002",
    status := "measured", artifact_ref := "artifact-1",
    observed_at := "2026-01-01T00:04:00Z" }

private def cost : CostEntry :=
  { identity := ident "cost-1", run_ref := "run-1", category := "machine_time",
    amount := "2.50", unit := "cpu_s", source := "synthetic-meter", coverage := "complete" }

private def assessment : Assessment :=
  { identity := ident "assessment-1", protocol_ref := "protocol-1",
    observation_refs := #["observation-1"], verdict := "pass", rule_used := "exact_v0" }

private def decision : PromotionDecision :=
  { identity := ident "decision-1", assessment_ref := "assessment-1",
    result := "promote", reason := "Synthetic threshold passed." }

private def relation : Relation :=
  { identity := ident "relation-1", source_ref := "observation-1",
    target_ref := "claim-1", kind := "support" }

private def ev (sequence : Nat) (kind time : String) (payload : Json) : Event :=
  { event_id := s!"event-{sequence}", version := 1,
    domain := "synthetic-computation", provenance := "synthetic://slean-v0", sequence, kind,
    actor := "synthetic-author", recorded_at := s!"2026-01-01T00:{time}:00Z",
    audience := "agent", payload }

def syntheticCase : CaseFile :=
  { schema_version := "0.1.0", semantics_version := "0.1.0",
    case_id := "synthetic-decision-1", version := 1,
    domain := "synthetic-computation", provenance := "synthetic://slean-v0",
    audience := "agent",
    question := { identity := ident "question-1", text := "Does a synthetic candidate exceed a fixed threshold?" },
    claim := { identity := ident "claim-1", text := "The synthetic metric exceeds 0.001 on the stated input." },
    events := #[
      ev 1 "protocol_frozen" "01" (toJson protocol),
      ev 2 "run_started" "02" (toJson run),
      ev 3 "artifact_registered" "03" (toJson artifact),
      ev 4 "observation_recorded" "04" (toJson observation),
      ev 5 "cost_recorded" "05" (toJson cost),
      ev 6 "assessment_recorded" "06" (toJson assessment),
      ev 7 "decision_recorded" "07" (toJson decision),
      ev 8 "relation_recorded" "08" (toJson relation)] }

#guard (replay syntheticCase).isOk
#guard (compareDecimal (parseDecimal "0.010" |>.toOption.get!)
  (parseDecimal "0.01" |>.toOption.get!)) == .eq
#guard (assessExact protocol observation).toOption == some "pass"

def main : IO Unit := IO.println (toJson (project syntheticCase "agent")).compress
```

Exécutez ces commandes pour résumer le grand résultat JSON :

```
lake env lean --run examples/Synthetic.lean |
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["case_id"], len(d["events"]))'
lake exe slean replay examples/valid.json 7 |
  python3 -c 'import json,sys; s=json.load(sys.stdin); print(len(s["event_ids"]), s["assessments"][0]["verdict"], s["decisions"][0]["result"])'
```

Résultats attendus : `synthetic-decision-1 8` et `7 pass promote`. Le programme typé émet huit événements visibles par l'agent ; la fixture JSON compte dix événements au total, dont deux réservés au propriétaire. Le préfixe sept contient l'évaluation et la décision. `tests/check.sh` compare octet par octet la sortie typée et la projection `agent` de la fixture. Ce contrôle porte sur la chaîne consignée ; il ne confirme ni la réalité de la mesure synthétique ni la correspondance entre l'empreinte et les octets de l'artefact.

*2. Comparer des décimaux à un seuil strict*

Problème : décider si une chaîne décimale égale au seuil figé, puis une valeur juste au-dessus, satisfont une règle stricte, sans arrondi en virgule flottante.

*Source complète : `examples/ExactThreshold.lean`*

```
import Slean

open Slean

private def identity (id : String) : Identity :=
  { id, version := 1, domain := "synthetic-computation",
    provenance := "synthetic://worked-examples", audience := "agent" }

private def protocol : FrozenProtocol :=
  { identity := identity "protocol-exact", claim_ref := "claim-exact",
    metric_id := "synthetic_delta", unit := "ratio", direction := "gte",
    threshold := "0.010", inclusive := false, data_scope := "synthetic input",
    evaluator_ref := "synthetic-evaluator", cost_cap := "1.00",
    cost_unit := "cpu_s", stop_rule := "one synthetic reading",
    frozen_at := "2026-01-01T00:00:00Z" }

private def reading (id value : String) : Observation :=
  { identity := identity id, run_ref := "run-exact", metric_id := "synthetic_delta",
    unit := "ratio", value := some value, status := "measured",
    artifact_ref := "artifact-exact", observed_at := "2026-01-01T00:01:00Z" }

def main : IO Unit := do
  match assessExact protocol (reading "equal" "0.0100"),
        assessExact protocol (reading "above" "0.0101") with
  | .ok equal, .ok above =>
    IO.println s!"equal={equal}; above={above}"
  | .error message, _ => throw (IO.userError message)
  | _, .error message => throw (IO.userError message)
```

Exécutez `lake env lean --run examples/ExactThreshold.lean`. Résultat attendu : `equal=fail; above=pass`. `0.0100` est exactement égal à `0.010`, tandis que `0.0101` est supérieur. `assessExact` compare une observation fournie à un protocole ; ce petit programme ne valide ni un journal, ni un artefact, ni la provenance de la mesure. Utilisez un `CaseFile` et `replay`, comme dans l'exemple 1, pour vérifier la chaîne de références consignée.

*3. Valider, projeter et préparer un export*

Problème : valider tout le dossier JSON synthétique avant de préparer un export versionné destiné à un agent. Le programme lit la fixture du dépôt depuis sa racine.

*Source complète : `examples/ValidateExport.lean`*

```
import Slean

open Lean Slean

def main : IO Unit := do
  let raw ← IO.FS.readFile "examples/valid.json"
  let json ← match Json.parse raw with
    | .ok value => pure value
    | .error message => throw (IO.userError message)
  let dossier ← match (fromJson? json : Except String CaseFile) with
    | .ok value => pure value
    | .error message => throw (IO.userError message)
  let fullState ← match replay dossier with
    | .ok state => pure state
    | .error diagnostic => throw (IO.userError diagnostic.message)
  let agentDossier := project dossier "agent"
  let agentState ← match replay agentDossier with
    | .ok state => pure state
    | .error diagnostic => throw (IO.userError diagnostic.message)
  let bundle := exportBundle agentDossier
  IO.println s!"validated={fullState.event_ids.size}; agent_events={agentState.event_ids.size}"
  IO.println s!"export={bundle.format}; lean={bundle.lean_version}"
```

Exécutez `lake env lean --run examples/ValidateExport.lean`. Résultat attendu :

```
validated=10; agent_events=8
export=slean-export/0.1.0; lean=4.28.0
```

Pour écrire puis revalider l'enveloppe complète de cette fixture synthétique, utilisez le CLI :

```
lake exe slean export examples/valid.json agent > /tmp/slean-agent-export.json
lake exe slean validate /tmp/slean-agent-export.json
```

La seconde commande renvoie `{"case_id":"synthetic-decision-1","events":8,"ok":true}`. La projection `agent` omet les événements réservés au propriétaire avant de produire l'export, mais un vrai export doit encore être relu avant partage : la validation ne décide pas si tout texte libre peut être divulgué.

*4. Séparer les résultats empiriques des reçus de preuve*

Problème : éviter qu'une affirmation formelle déclarée soit considérée comme vérifiée par le noyau simplement parce que son statut d'entrée le dit. Ce programme fixe volontairement `status := "kernel_checked"` sur une référence concordant avec le théorème local ; `proofReceipt` renvoie quand même `declared`.

*Source complète : `examples/FormalBoundary.lean`*

```
import Slean

open Lean Slean

private def formalIdentity : Identity :=
  { id := "formal-claim-demo", version := 1, domain := "synthetic-computation",
    provenance := "synthetic://worked-examples", audience := "agent" }

private def formalClaim : FormalClaimRef :=
  { identity := formalIdentity,
    declaration := checkedDeclaration, statement := checkedStatement,
    toolchain := checkedToolchain, status := "kernel_checked" }

def main : IO Unit := do
  let receipt := proofReceipt formalClaim
  let status := (receipt.getObjValAs? String "status").toOption.getD "missing"
  let eligible := (receipt.getObjValAs? Bool "attestation_eligible").toOption.getD false
  IO.println s!"eligible={eligible}; status={status}"
```

Exécutez `lake env lean --run examples/FormalBoundary.lean`. Résultat attendu : `eligible=true; status=declared`. Une déclaration et une version de Lean concordantes rendent l'affirmation admissible à une *attestation séparée* sur un build propre ; ce programme ne produit pas cette attestation. Le théorème est conditionnel et relie la décision de promotion consignée à des enregistrements antérieurs. Ni ce théorème local ni un `pass` empirique ne prouvent que la mesure, l'évaluateur ou l'affirmation scientifique sont vrais.

*5. Revoir une décision de demande avec des données horaires publiques*

Problème : comparer deux prédicteurs simples du nombre de locations par heure sur une année ultérieure, puis inspecter ce que Slean consigne. Il s'agit d'un *protocole rétrospectif pédagogique rédigé pour Slean*, pas d'un protocole de l'UCI ni de Capital Bikeshare. Il a été [figé au commit `7c5bb24`](https://github.com/romainsimon/slean/commit/7c5bb24f8f07e73db76b8bf37ec12d7ccec2a283) le `2026-09-25T07:10:52Z`, avant le début de l'unique évaluation consignée à `2026-09-25T07:14:43Z`.

Source : Hadi Fanaee-T, [Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike%2Bsharing%2Bdataset), UCI Machine Learning Repository (2013), [DOI 10.24432/C5W894](https://doi.org/10.24432/C5W894), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). L'archive ZIP officielle non modifiée contient 279 992 octets, SHA-256 `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401` ; son membre `hour.csv` a pour SHA-256 `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`. Le dépôt conserve le petit résultat dérivé, pas le CSV. La page UCI annonce 17 389 instances ; le fichier `hour.csv` épinglé contient 17 379 lignes de données. Le script vérifie ce compte et les deux empreintes.

La règle figée entraîne une moyenne globale sur les 8 645 heures consignées en 2011 comme référence, puis une moyenne par heure de la journée sur ces mêmes lignes comme candidat. Elle évalue les deux une seule fois sur les 8 734 heures tenues à l'écart en 2012. La mesure est le MAE de référence moins le MAE du candidat, en vélos par heure consignée, arrondie à six décimales au pair le plus proche ; le seuil illustratif de promotion est `>= 5.000000` vélos/heure. Le plafond CPU local est `5.000000000 cpu_s`, téléchargement exclu.

L'exécution consignée mesure un MAE de référence de `168.251927`, un MAE candidat de `118.157229` et une amélioration de `50.094698` vélos/heure, avec `0.122995000 cpu_s`. Slean accepte le dossier de huit événements et rejoue `pass` puis `promote` *dans ce seul cadre illustratif*. Le résultat `examples/uci-bike-sharing/result.json` a pour SHA-256 `dc45fa164d3125d58e6769b9480c577aaa4d68e9ea55a10886eb7aaf8caf540a` ; son calcul complet et la référence source figurent dans `tools/evaluate_uci_bike_sharing.py` et le protocole figé `examples/uci-bike-sharing/protocol.json`.

Pour refaire le calcul, téléchargez uniquement l'archive officielle et utilisez le script épinglé. Les MAE numériques doivent être identiques ; le temps d'exécution et l'empreinte de sortie changeront lors d'une nouvelle exécution.

```
curl -LfsS 'https://archive.ics.uci.edu/static/public/275/bike%2Bsharing%2Bdataset.zip' -o /tmp/slean-uci-bike-sharing.zip
shasum -a 256 /tmp/slean-uci-bike-sharing.zip
python3 tools/evaluate_uci_bike_sharing.py --archive /tmp/slean-uci-bike-sharing.zip --output-dir /tmp/slean-uci-repeat
lake exe slean validate /tmp/slean-uci-repeat/case.json
lake exe slean replay /tmp/slean-uci-repeat/case.json 8
```

Le dossier versionné `examples/uci-bike-sharing/case.json` se valide aussi sans réseau : `lake exe slean validate examples/uci-bike-sharing/case.json` renvoie `{"case_id":"uci-bike-hourly-2011-2012-mae-v1","events":8,"ok":true}`. Son préfixe `5` contient l'amélioration de MAE mesurée ; le préfixe `8` ajoute le coût, l'évaluation et la décision bornée.

Les champs UCI `dteday` et `hr` désignent les heures locales historiques de 2011–2012 ; la source n'indique pas de fuseau horaire, donc l'évaluateur ne les convertit pas en UTC. Les dates des événements Slean en 2026 décrivent *l'évaluation rétrospective*, pas les locations d'origine. Slean vérifie les références, l'ordre consigné, le seuil décimal exact et le plafond CPU déclaré. Il ne calcule pas indépendamment les empreintes UCI ni le MAE, ne certifie pas les mesures et ne recommande pas d'exploiter une flotte de vélos avec ce prédicteur. L'évaluateur Python épinglé et l'archive source restent dans la chaîne de confiance.

# Limites et état du développement
%%%
file := "limites-et-etat-du-developpement"
tag := "limites-et-etat-du-developpement"
%%%

*Slean vérifie ici :* la forme versionnée du dossier, les identifiants et références, l'ordre causal du journal, la comparaison décimale locale, le plafond de coût déclaré, la règle de promotion, les références des portes ET/OU et la projection d'audience. Il peut montrer une erreur précise ou conserver un résultat indéterminé.

*Slean ne vérifie pas ici :* que la mesure a été réellement prise, que les octets d'un artefact sont authentiques, que l'horloge externe ou l'évaluateur est fiable, qu'une porte ET/OU démontre sa cible, que la décision humaine est judicieuse, ou que l'affirmation scientifique est vraie. Le théorème Lean local porte sur une propriété conditionnelle du mécanisme, pas sur ces faits empiriques. Aucune vérification indépendante de preuve n'est configurée.

Ce site est un prototype local antérieur à la publication. Ses cas Lean d'origine sont synthétiques ; le cas Bike Sharing est une comparaison pédagogique rétrospective mesurée sur des données publiques sous licence. La licence publique de Slean, la visibilité du dépôt, le domaine et les intégrations restent des décisions distinctes. La construction exécute les tests et compile les exemples avant de générer le manuel. `build-info.json` indique le commit source, la propreté de l'arbre lorsque les métadonnées Git sont disponibles, le schéma, Lean et le tag sélectionné ; sans ces métadonnées, `source_tree_clean` vaut `null` car la propreté est inconnue. Un build sans tag reste une prévisualisation de développement.
