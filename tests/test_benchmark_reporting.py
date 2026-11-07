import hashlib
import json
from zipfile import ZipFile
import pytest


def fixture_bundle(path):
    h=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    config={'years':[2024],'linear_arms':['S'],'tree_arms':[]}
    audit={'input_rows':4,'eligible_rows':4,'windows':[{'year':2024,'asof_train_rows':2,'evaluation_rows':2}]}
    result={'schema_version':'matched_text_benchmark.v1','status':'completed_pending_review',
            'configuration':config,'input_rows':4,'eligible_rows':4,
            'windows':[{'year':2024,'train_rows':2,'test_rows':2,'test_row_identity_sha256':'rows'}],
            'models':[{'year':2024,'family':f,'arm':a,'row_identity_sha256':'rows',
                       'metrics':{'rows':2},'fit':{'train_rows':2,'test_rows':2}}
                      for f,a in [('baseline','B0'),('baseline','B1'),('linear','S')]]}
    (path/'benchmark.json').write_text(json.dumps(result))
    (path/'availability_audit.json').write_text(json.dumps(audit))
    (path/'status.json').write_text(json.dumps({'status':'completed_pending_review','model_count':3}))
    with ZipFile(path/'source_snapshot.zip','w') as z:
        z.writestr('src/a.py','source')
    provenance={'configuration':config,'benchmark_sha256':h(path/'benchmark.json'),
                'audit_sha256':h(path/'availability_audit.json'),
                'source_snapshot_sha256':h(path/'source_snapshot.zip'),
                'source_hashes':{'src/a.py':hashlib.sha256(b'source').hexdigest()}}
    (path/'provenance.json').write_text(json.dumps(provenance))
    review={'status':'accepted','benchmark_sha256':h(path/'benchmark.json'),
            'provenance_sha256':h(path/'provenance.json'),'audit_sha256':h(path/'availability_audit.json')}
    return result,provenance,review


def test_reader_requires_review_and_matching_artifact_hashes(tmp_path):
    from src.benchmark_reporting import load_bundle
    result,_,review=fixture_bundle(tmp_path)
    with pytest.raises(ValueError,match='accepted'):
        load_bundle(tmp_path)
    (tmp_path/'review_status.json').write_text(json.dumps(review))
    assert load_bundle(tmp_path)['benchmark']==result
    (tmp_path/'benchmark.json').write_text('{}')
    with pytest.raises(ValueError,match='hash'):
        load_bundle(tmp_path)


@pytest.mark.parametrize('damage',['empty','duplicate','rows','status','audit','sources'])
def test_reader_rejects_incomplete_or_inconsistent_bundle_even_with_matching_hash(tmp_path,damage):
    from src.benchmark_reporting import load_bundle
    result,provenance,_=fixture_bundle(tmp_path)
    if damage=='empty': result['models']=[]
    if damage=='duplicate': result['models'][2]=result['models'][0]
    if damage=='rows': result['models'][0]['metrics']['rows']=1
    if damage=='status': (tmp_path/'status.json').write_text('{"status":"failed"}')
    if damage=='audit':
        audit=json.loads((tmp_path/'availability_audit.json').read_text())
        audit['windows'][0]['evaluation_rows']=1
        (tmp_path/'availability_audit.json').write_text(json.dumps(audit))
        provenance['audit_sha256']=hashlib.sha256((tmp_path/'availability_audit.json').read_bytes()).hexdigest()
    if damage=='sources': provenance['source_hashes']['src/a.py']='wrong'
    (tmp_path/'benchmark.json').write_text(json.dumps(result))
    provenance['benchmark_sha256']=hashlib.sha256((tmp_path/'benchmark.json').read_bytes()).hexdigest()
    (tmp_path/'provenance.json').write_text(json.dumps(provenance))
    with pytest.raises(ValueError):
        load_bundle(tmp_path,require_review=False)
