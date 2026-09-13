#!/usr/bin/env python3
"""Build a reproducible, explicitly post hoc notebook for unused-evidence analysis."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "DataFaultBench_Exploratory_Reanalysis_v1.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()
nb["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb["metadata"]["language_info"] = {"name": "python", "version": "3"}

cells = []
cells.append(
    nbf.v4.new_markdown_cell(
        "# DataFaultBench exploratory reanalysis\n\n"
        "## tl;dr\n\n"
        "This notebook reuses only frozen Study I artifacts. It does **not** alter the "
        "confirmatory candidate, test, or conclusion. The main descriptive findings are: "
        "(1) the marginal losses from numerical outliers and label flips transferred almost "
        "unchanged, while the joint-loss composition did not; (2) only 11 calibration domains "
        "support every candidate, yet the original winner remains first on this common support; "
        "and (3) the 125 non-retained candidates form useful curation-audit evidence."
    )
)
cells.append(
    nbf.v4.new_markdown_cell(
        "## Context & Methods\n\n"
        "### Key Assumptions\n\n"
        "- All analyses are post hoc and descriptive.\n"
        "- Domain is the aggregation unit; corruption replicates are averaged within domain.\n"
        "- The selected Study I candidate is never replaced.\n"
        "- Review-category aggregation below is a transparent analytical taxonomy over the "
        "frozen primary reasons, not a new eligibility decision."
    )
)
cells.append(
    nbf.v4.new_code_cell(
        "from pathlib import Path\n"
        "import csv, json, collections\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "from scipy import stats\n\n"
        "HERE = Path.cwd()\n"
        "PROJECT = HERE.parent if HERE.name == 'analysis' else HERE\n"
        "WORKSPACE = PROJECT.parent\n"
        "PUBLIC = WORKSPACE / 'retrieved/original/extracted/DataFaultBench_Public_Reproducibility_v1'\n"
        "assert PUBLIC.exists(), PUBLIC\n"
        "plt.rcParams.update({'figure.figsize': (8.0, 4.6), 'axes.spines.top': False, "
        "'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': 0.2})"
    )
)
cells.append(nbf.v4.new_markdown_cell("## Data\n\nLoad frozen calibration and final-test cells."))
cells.append(
    nbf.v4.new_code_cell(
        "cal_raw = json.loads((PUBLIC/'calibration_evidence/calibration_cells.json').read_text())['cells']\n"
        "fin_raw = json.loads((PUBLIC/'final_test_evidence/final_test_cells.json').read_text())['cells']\n"
        "cal, fin = pd.DataFrame(cal_raw), pd.DataFrame(fin_raw)\n"
        "for frame in (cal, fin):\n"
        "    for scenario in ['clean','a_only','b_only','joint']:\n"
        "        frame[scenario] = frame['utilities'].map(lambda value: value[scenario])\n"
        "    frame['loss_a'] = frame.clean - frame.a_only\n"
        "    frame['loss_b'] = frame.clean - frame.b_only\n"
        "    frame['loss_joint'] = frame.clean - frame.joint\n"
        "{'calibration_cells': len(cal), 'calibration_domains': cal.task_id.nunique(), "
        " 'final_cells': len(fin), 'final_domains': fin.task_id.nunique()}"
    )
)
cells.append(nbf.v4.new_markdown_cell("## Results\n\n### 1. The marginal faults transferred; their composition did not"))
cells.append(
    nbf.v4.new_code_cell(
        "selected = cal[(cal.model=='extra_trees') & "
        "(cal.defect_pair=='numeric_outlier+label_flip') & "
        "(cal.process=='independent') & (cal.severity=='0.30+0.30')]\n\n"
        "def component_table(frame, partition):\n"
        "    domains = frame.groupby(['task_id','dataset_name'], as_index=False).agg(\n"
        "        outlier_loss=('loss_a','mean'), label_flip_loss=('loss_b','mean'),\n"
        "        joint_loss=('loss_joint','mean'), interaction=('interaction','mean'))\n"
        "    out = domains.drop(columns=['task_id','dataset_name']).mean().rename(partition)\n"
        "    return domains, out\n\n"
        "cal_domains, cal_components = component_table(selected, 'Calibration')\n"
        "fin_domains, fin_components = component_table(fin, 'Final test')\n"
        "components = pd.concat([cal_components, fin_components], axis=1).T\n"
        "components_pp = (100*components).rename(columns={\n"
        "    'outlier_loss':'Outlier loss', 'label_flip_loss':'Label-flip loss',\n"
        "    'joint_loss':'Joint loss', 'interaction':'Interaction'})\n"
        "components_pp.round(3)"
    )
)
cells.append(
    nbf.v4.new_code_cell(
        "ax = components_pp[['Outlier loss','Label-flip loss','Joint loss']].T.plot(\n"
        "    kind='bar', color=['#2f6fae','#c46f3d'], rot=0)\n"
        "ax.set_title('Marginal losses transferred, but joint loss increased')\n"
        "ax.set_ylabel('Balanced-accuracy loss (percentage points)')\n"
        "ax.set_xlabel('')\n"
        "plt.tight_layout(); plt.show()"
    )
)
cells.append(
    nbf.v4.new_markdown_cell(
        "The outlier loss was 1.27 versus 1.35 percentage points, and the label-flip "
        "loss was 4.43 versus 4.37 points. Their marginal sum was therefore almost "
        "unchanged. The joint loss increased from 4.10 to 5.27 points, accounting "
        "algebraically for the interaction attenuation from 1.60 to 0.44 points. "
        "This supports a composition-transfer interpretation rather than a claim that "
        "the individual faults became weaker."
    )
)
cells.append(nbf.v4.new_markdown_cell("### 2. Structural eligibility changes the comparison population"))
cells.append(
    nbf.v4.new_code_cell(
        "candidate_keys = ['model','defect_pair','process','severity']\n"
        "domain_candidates = cal.groupby(candidate_keys+['task_id'], as_index=False).interaction.mean()\n"
        "candidate_domain_sets = domain_candidates.groupby(candidate_keys).task_id.apply(set)\n"
        "common_domains = set.intersection(*candidate_domain_sets)\n"
        "full = domain_candidates.groupby(candidate_keys).interaction.agg(['count','mean','std'])\n"
        "full['score'] = full['mean'].abs()/(full['std']/np.sqrt(full['count']))\n"
        "common = domain_candidates[domain_candidates.task_id.isin(common_domains)].groupby(candidate_keys).interaction.agg(['count','mean','std'])\n"
        "common['score'] = common['mean'].abs()/(common['std']/np.sqrt(common['count']))\n"
        "winner = ('extra_trees','numeric_outlier+label_flip','independent','0.30+0.30')\n"
        "pd.DataFrame({\n"
        "    'eligible_domains_by_pair': domain_candidates.groupby('defect_pair').task_id.nunique(),\n"
        "}).join(pd.Series({'common_to_all_36':len(common_domains)}, name='common_support'), how='outer'), "
        "(full.loc[winner,'score'], common.loc[winner,'score'], common.score.rank(ascending=False).loc[winner])"
    )
)
cells.append(
    nbf.v4.new_markdown_cell(
        "Only 11 domains were eligible for every one of the 36 candidates, below the "
        "original 12-domain formal-selection threshold. Therefore the common-support "
        "ranking is sensitivity evidence only. Nevertheless, the frozen winner remained "
        "ranked first on those 11 domains (score 3.29 versus 3.59 in the original analysis), "
        "which argues against eligibility composition as the sole explanation for selection."
    )
)
cells.append(nbf.v4.new_markdown_cell("### 3. Turn rejected candidates into curation-audit evidence"))
cells.append(
    nbf.v4.new_code_cell(
        "review_dir = PUBLIC/'data_governance/source_review_evidence'\n"
        "review_order = [\n"
        " 'combined_source_review__provisionally_eligible.csv',\n"
        " 'expanded_candidate_source_review__candidate_source_license_independence_review.csv',\n"
        " 'openml_active_classification_pool__source_review__source_license_independence_review.csv',\n"
        " 'openml_active_classification_pool__deep_source_review__candidate_source_license_independence_review.csv',\n"
        " 'openml_active_classification_pool__followup_source_review__followup_candidate_review.csv',\n"
        " 'openml_active_classification_pool__remaining_domain_round2__final_candidate_review.csv',\n"
        " 'openml_active_classification_pool__remaining_domain_round3__final_candidate_review.csv',\n"
        " 'openml_active_classification_pool__remaining_domain_round4__final_candidate_review.csv']\n"
        "rank = {name:index for index,name in enumerate(review_order)}\n"
        "histories = collections.defaultdict(list)\n"
        "for path in review_dir.glob('*.csv'):\n"
        "    with path.open(encoding='utf-8-sig', newline='') as handle:\n"
        "        for row in csv.DictReader(handle):\n"
        "            item = {\n"
        "              'file':path.name, 'task':str(row.get('task_id') or '').strip(),\n"
        "              'dataset':str(row.get('dataset_id') or '').strip(),\n"
        "              'name':str(row.get('dataset_name') or row.get('name') or '').strip(),\n"
        "              'decision':str(row.get('decision') or ('eligible' if 'provisionally_eligible' in path.name else '')).strip(),\n"
        "              'reason':str(row.get('primary_reason') or row.get('license_review_status') or '').strip(),\n"
        "              'url':str(row.get('evidence_url') or row.get('canonical_source_url') or '').strip(),\n"
        "              'note':str(row.get('review_note') or '').strip()}\n"
        "            key = ('task',item['task']) if item['task'] else (('dataset',item['dataset']) if item['dataset'] else ('name',item['name'].lower()))\n"
        "            histories[key].append(item)\n"
        "reviews = [max(items, key=lambda item:rank.get(item['file'],-1)) for items in histories.values()]\n"
        "review = pd.DataFrame(reviews)\n\n"
        "def reason_category(row):\n"
        "    text=(row.reason+' '+row.note).lower()\n"
        "    if 'duplicate' in text: return 'Duplicate/source overlap'\n"
        "    if any(x in text for x in ['license','licence','rights reserved','use conditions']): return 'Provenance/license'\n"
        "    if any(x in text for x in ['image','text_origin','text or web']): return 'Image/text-derived'\n"
        "    if any(x in text for x in ['time','temporal','longitudinal','panel','judicial']): return 'Temporal dependence'\n"
        "    if any(x in text for x in ['leakage','target']): return 'Target/identifier leakage'\n"
        "    if any(x in text for x in ['group','dyad','participant','entity','respondent','independ']): return 'Non-IID/grouped units'\n"
        "    if any(x in text for x in ['synthetic','oversampling','generated']): return 'Synthetic/dependence'\n"
        "    return 'Other unresolved'\n"
        "review['category'] = review.apply(reason_category, axis=1)\n"
        "decision_counts = review.decision.value_counts().reindex(['eligible','excluded','blocked'])\n"
        "category_counts = review[review.decision!='eligible'].category.value_counts()\n"
        "decision_counts, category_counts"
    )
)
cells.append(
    nbf.v4.new_code_cell(
        "fig, axes = plt.subplots(1,2,figsize=(11,4.4))\n"
        "decision_counts.plot(kind='bar',ax=axes[0],color=['#2f7d62','#c46f3d','#777777'],rot=0)\n"
        "axes[0].set_title('Only 55 of 180 reviewed candidates were retained')\n"
        "axes[0].set_ylabel('Unique candidate domains')\n"
        "category_counts.sort_values().plot(kind='barh',ax=axes[1],color='#4f77a3')\n"
        "axes[1].set_title('Why 125 candidates were not retained')\n"
        "axes[1].set_xlabel('Unique candidate domains')\n"
        "plt.tight_layout(); plt.show()\n"
        "review.groupby('decision').agg(n=('decision','size'), evidence_url=('url',lambda x:(x!='').sum()), documented_note=('note',lambda x:(x!='').sum()))"
    )
)
cells.append(
    nbf.v4.new_markdown_cell(
        "The discarded candidates are not valid additions to the 55-domain inferential population, "
        "but they are useful as an audit corpus. Across 180 unique reviewed candidates, 55 were "
        "retained, 71 excluded, and 54 blocked. Every excluded/blocked candidate has a documented "
        "note, and 101 of 125 have an evidence URL. A release should preserve the frozen fine-grained "
        "reason and present the broad taxonomy only as a secondary summary."
    )
)
cells.append(
    nbf.v4.new_markdown_cell(
        "## Takeaways\n\n"
        "1. **Strongest manuscript extension:** distinguish marginal-effect transfer from "
        "interaction/composition transfer.\n"
        "2. **Strongest tool/data extension:** release the 180-candidate curation audit corpus, "
        "with rejected domains used as documented negative cases rather than model evidence.\n"
        "3. **Best sensitivity result:** structural eligibility changes the estimand, but the "
        "original winner remains first on the 11-domain common support.\n"
        "4. **Boundary:** none of these post hoc analyses converts the nonsignificant sealed "
        "final test into a positive confirmatory result."
    )
)

nb["cells"] = cells
nbf.write(nb, OUT)
print(OUT)
