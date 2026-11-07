"""Build a new deck storyline from an explicitly reviewed benchmark bundle."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from src.benchmark_reporting import load_bundle


def build_story(bundle_path: Path) -> dict:
    bundle=load_bundle(bundle_path)
    report=bundle['benchmark']
    audit=bundle['audit']
    path=Path(__file__).parent
    story=json.loads((path/'storyline.json').read_text())
    slides=story['slides']
    years=report['configuration']['years']
    latest=max(years)
    models={(m['year'],m['family'],m['arm']):m for m in report['models']}
    pairs={(p['year'],p['family'],p['baseline'],p['candidate'],p['metric'],p['resampling_unit']):p
           for p in report['paired_comparisons']}
    source=str(bundle_path.resolve().relative_to(ROOT)/'benchmark.json')
    audit_source=str(bundle_path.resolve().relative_to(ROOT)/'availability_audit.json')
    story['title']='What narrative text adds to funding-speed forecasts'
    story['benchmark_sha256']=bundle['provenance']['benchmark_sha256']
    slides[0].update(title='What narrative text adds\nto funding-speed forecasts',
                     subtitle='Post-competition research: matched full-data forecasts',
                     status='Reviewed post-competition predictive extension',
                     evidence=f"{audit['input_rows']:,} input records; {audit['eligible_rows']:,} valid completed durations; {len(report['models'])} model/arm windows.")
    slides[0]['notes']+=' The new matched study is separate from the original competition results. The retrospective evaluation does not become an untouched test because we changed the protocol.'
    slides[0]['sources'].append(source)
    slides[1].update(title='Use the matched evidence to choose the next test',
                     items=[['Audit','Training outcomes and completed-cohort membership precede each cutoff.'],
                            ['Compare','Structure and text use matching rows within each model family.'],
                            ['Validate','Check text meaning and intervention feasibility before a pilot.']],
                     message='The next decision concerns measurement and intervention, informed by a completed comparison.',
                     status='Recommendation after the matched benchmark',
                     evidence='Availability audit and fixed-config comparisons completed; no measured editing benefit.',
                     notes='The first two research steps are now completed. This does not remove completed-record selection, snapshot-field uncertainty or construct validity questions. Decide what the remaining information gaps justify before choosing a writing or allocation policy.',
                     sources=[source,audit_source,'docs/6_matched_text_results.md'])
    slides[2]['notes']+=' The new as-of training audit removes pre-cutoff postings whose completed membership was not yet known; the primary August snapshot is preserved.'
    slides[2]['sources'].append(audit_source)
    gains=[pairs[y,'linear','S','S+M+L+R','mae_days','calendar_month']['gain'] for y in years]
    country_crossings=sum(pairs[y,'linear','S','S+M+L+R','mae_days','country']['interval_95'][0]<=0<=
                          pairs[y,'linear','S','S+M+L+R','mae_days','country']['interval_95'][1] for y in years)
    slides[4].update(title='Text improves linear forecasts in all five years',layout='research_benchmark',
                     years=years,series=[{'name':'Structure only','values':[models[y,'linear','S']['metrics']['mae_days'] for y in years],'color':'#596271'},
                                         {'name':'Structure + text','values':[models[y,'linear','S+M+L+R']['metrics']['mae_days'] for y in years],'color':'#237F80'}],
                     gainLabel=f'{statistics.median(gains):.3f}',
                     aucLabel=f"{models[latest,'linear','S+M+L+R']['metrics']['roc_auc']-models[latest,'linear','S']['metrics']['roc_auc']:+.4f}",latestYear=latest,
                     message='Matched gains quantify additional predictive information; they are not the effects of editing.',
                     status='New full-data retrospective benchmark',
                     evidence='Sparse Ridge/logistic family, fixed configurations, as-of training cohorts. Annual rows and exact metrics are in the reviewed bundle.',
                     visual='Native grouped MAE chart for all five years, with matched structure/text inputs.',
                     action='Assess the size and temporal stability of added predictive information.',
                     notes='Compare structure-only and structure-plus-text within the same sparse linear family, using the same rows, outcomes and cutoffs. TF-IDF is fitted on each training window only. The side callout is the median of annual MAE gains, not a loan-weighted pooled estimate. The AUC change is text-added minus structure-only in the latest observed year: a negative value means ranking declined even though duration MAE improved. These fixed models are not tuned winners. Description contents may encode context as well as framing.',
                     sources=[source,'docs/6_matched_text_results.md'])
    rows=[]
    for year in years:
        a=pairs[year,'linear','S','S+M+L+R','mae_days','calendar_month']
        b=pairs[year,'histogram_boosting','S','S+M+L','mae_days','calendar_month']
        interval=lambda x:f"[{x['interval_95'][0]:.3f}, {x['interval_95'][1]:.3f}]" if x['interval_95'] else 'Unavailable'
        rows.append([str(year),f"{a['gain']:.3f}",interval(a),f"{b['gain']:.3f}",interval(b)])
    slides[5].update(title='Read the added-text gain with its uncertainty',layout='text_gain',
                     columns=['Year','Linear gain','Month 95% interval','Tree gain','Month 95% interval'],
                     widths=[90,160,340,160,386],rows=rows,
                     status='New matched comparisons; pointwise fixed-model sensitivity intervals',
                     message=f'Country-resampling intervals include zero in {country_crossings} of {len(years)} linear comparisons; read both sensitivity checks.',
                     evidence='Linear adds M+L+R; trees add M+L only. Positive gain means lower MAE in days. Month-cluster bootstrap uses 1,000 draws.',
                     visual='Native table of paired gains and month-block sensitivity intervals, with units.',
                     action='Choose a practical threshold with decision owners; do not infer an intervention return.',
                     notes='Each gain subtracts candidate absolute error from the structure-only error on the same records. Whole calendar-month blocks are resampled, preserving paired losses and weighting by record count. These are fixed-model sensitivity intervals, not causal intervals or retraining uncertainty. Annual windows have few independent month blocks. The notebook also shows country sensitivities, paired Brier gains and S+P versus S+P+text comparisons. P remains an unvalidated programme-text proxy.',
                     sources=[source,'docs/5_ml_refinement_plan.md'])
    slides[8]['rows'][1]=['Matched text benchmark','Full-data comparisons and stability diagnostics','Interpret gains and remaining measurement gaps']
    slides[8]['rows'][0]=['Context and content audit','Outcome maturity quantified; historical field versions missing','Request provenance and validate text measures']
    slides[8]['action']='Prioritise construct validation and the feasibility of a defined pilot.'
    slides[8]['notes']='The audit and matched comparison are completed. They support a decision about further measurement and feasibility work, not a claim that changing text will improve funding. All-listing validation and an agreed operational purpose are still required for allocation tools. A model identifying slow loans does not identify who benefits from attention.'
    calibration=models[latest,'linear','S+M+L+R']['calibration']
    bins=[b for b in calibration if b['count']]
    slides[9].update(title='Ranking and probability quality need separate checks',layout='calibration',
                     binLabels=[f"{int(b['lower']*100)}–{int(b['upper']*100)}%" for b in bins],
                     series=[{'name':'Mean prediction','values':[b['mean_probability'] for b in bins],'color':'#596271'},
                             {'name':'Observed 24-hour completion','values':[b['observed_rate'] for b in bins],'color':'#237F80'}],
                     countCaption='Bin counts (left to right): '+', '.join(f"{b['count']:,}" for b in bins),
                     status=f'{latest} observed completed records; sparse linear S+M+L+R',
                     message='A ranking score cannot establish reliable probabilities for all new listings.',
                     evidence='Equal-width probability bins; empty bins omitted. Brier/log loss, counts, tail errors and group diagnostics are in the notebook.',
                     visual='Native line chart comparing predicted and observed probability within fixed bins.',
                     action='Inspect reliability, coverage and the population before considering an operational queue.',
                     notes='This diagnostic uses the latest observed year and the prespecified text-added sparse linear model. Predictions are compared with observed completion within 24 hours in the same probability bins, with counts shown below. Empty bins are omitted. The notebook compares both model families and shows duration-tail and novelty diagnostics. No calibration model has been fitted and no all-listing deployment evaluation has been performed.',
                     sources=[source,'https://scikit-learn.org/stable/modules/calibration.html'])
    slides[11].update(title='Validate the proposed lever before running a pilot',
                      message='The retrospective comparison is complete; intervention benefit remains the next evidence gap.',
                      action='Validate narrative constructs and agree a feasible intervention design.',
                      notes='The as-of audit and matched full-data comparison are completed. Next validate the constructs, request historical field/exposure information and assess whether a factual presentation pilot is feasible. Agree its endpoint, assignment, practical threshold and guardrails before launch. The existing observational results do not establish the outcome of that experiment.')
    slides[11]['stages']=[['Validate','Research / data','Review constructs and historical field availability.'],['Design','Platform / partners','Agree feasibility, endpoint, assignment and power.'],['Test','Participating partners','Measure the defined intervention and guardrails.'],['Decide','Decision owners','Use practical benefit and uncertainty to choose.']]
    slides[12]['rows'][-1]=['November matched benchmark','As-of full-data prediction and paired text gains','New retrospective results on slides 5, 6 and 10']
    slides[12]['rows'][0][2]='Descriptive/explanatory context on slides 3/7; appendix 14'
    for row in slides[12]['rows']:
        if row[0]=='Simpler notebooks':
            row[0]='Historical simpler notebooks'
    slides[12]['notes']+=' This update adds the reviewed November predictive extension and preserves the earlier research-design deck as a separate artifact.'
    slides[12]['sources'].append(source)
    slides[14]['rows'][0]=['“No narrative features needed”','Use the completed matched comparison, with model, window and uncertainty.']
    slides[14]['notes']+=' The missing comparison has now been run; its estimates remain predictive information gains.'
    slides[15]['rows']=[['1','Human validation of narrative constructs','Freeze development codebook; audit later-period transfer'],
                        ['2','Historical listing and exposure data','Verify field versions and marketplace context'],
                        ['3','Operational calibration or interval forecasts','Agree population and decision; validate on earlier temporal data'],
                        ['4','Prospective factual presentation pilot','Agree endpoint, assignment, power and guardrails'],
                        ['5','All-listing survival extension','Obtain unsuccessful/censored histories and observation rules']]
    slides[15]['evidence']='Next experiments after the matched study; no new annotations, survival data or pilot results exist.'
    slides[15]['notes']='Further model complexity should answer a documented need. The full matched study does not validate the psychological meaning of text features, produce a calibrated deployment tool or identify a writing intervention. Human measurement and missing process data are the next priorities.'
    return story


def write_brief(story: dict, destination: Path) -> None:
    parts=['# Slide-by-slide briefing: matched benchmark update\n\n',
           'Post-competition update, 2026-11-02. Twelve core slides plus four appendix slides. The previous research-design deck remains preserved.\n\n']
    for i,s in enumerate(story['slides'],1):
        sources='; '.join(f'[{u.split("/")[2]}]({u})' if u.startswith('http') else f'`{u}`' for u in s['sources'])
        parts.append(f"## {i}. {s['title'].replace(chr(10),' ')}\n\n**Message:** {s['message']}\n\n**Reader decision:** {s['action']}\n\n**Evidence status:** {s['status']}. {s['evidence']}\n\n**Exhibit:** {s['visual']}\n\n**Speaker briefing:** {s['notes']}\n\n**Sources:** {sources}.\n\n")
    destination.write_text(''.join(parts))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    args=parser.parse_args()
    story=build_story(args.bundle)
    here=Path(__file__).parent
    (here/'storyline_benchmark.json').write_text(json.dumps(story,indent=2,ensure_ascii=False)+'\n')
    write_brief(story,here.parent/'slide_brief_benchmark.md')
