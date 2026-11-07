import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL, fileURLToPath} from 'node:url';

// Set ARTIFACT_NODE_MODULES to the bundled runtime returned by
// load_workspace_dependencies. No analysis data or network access is needed.
const modules = process.env.ARTIFACT_NODE_MODULES;
const skillDir = process.env.PRESENTATION_SKILL_DIR;
const runtimePython = process.env.ARTIFACT_PYTHON;
if (!modules || !skillDir || !runtimePython) throw new Error('Set the three documented runtime variables.');
process.env.RUNTIME_NODE_MODULES = modules;
const requireRuntime = createRequire(path.join(modules, '..', 'package.json'));
const {Presentation, PresentationFile} = await import(pathToFileURL(requireRuntime.resolve('@oai/artifact-tool')).href);
const {finalizePresentation, applyPresentationChartFont} = await import(pathToFileURL(path.join(skillDir, 'container_tools/artifact_tool_utils.mjs')).href);
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../..');
const work = path.resolve(here, '..');
const build = path.join(work, '.build');
const out = path.join(work, 'output');
await fs.mkdir(build, {recursive:true});
await fs.mkdir(out, {recursive:true});
await fs.mkdir(path.join(build, 'previews'), {recursive:true});
const storyPath = process.env.DECK_STORYLINE || path.join(here, 'storyline.json');
const story = JSON.parse(await fs.readFile(storyPath, 'utf8'));
const saved = JSON.parse(await fs.readFile(path.join(root, 'reports/generated_full_dataset/analysis_summary.json'), 'utf8'));
const p = Presentation.create({slideSize:{width:1280,height:720}});
const C = {paper:'#FBFAF6', ink:'#1C2333', muted:'#596271', teal:'#237F80', yellow:'#FFDD04', line:'#D4D8DB', pale:'#F0EEE5'};
const FONT = 'DM Sans';
let seq=0;
function text(s,value,x,y,w,h,size=26,bold=false,color=C.ink){
  const sh=s.shapes.add({name:`text-${++seq}`,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=value;
  sh.text.style={fontFamily:FONT,typeface:FONT,fontSize:size,bold,color,verticalAlignment:'top',wrap:true,insets:0};
  return sh;
}
function table(s,values,widths,y=214,h=340,size=23){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:72,top:y,width:1136,height:h,columnWidths:widths,values});
 t.borders.assign({fill:C.line,width:0.6,style:'solid'});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{typeface:FONT,fontSize:size,color:C.ink},margins:{left:14,right:14,top:6,bottom:6},anchor:'center'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c); cell.fill=r===0?C.ink:(r%2===0?C.pale:C.paper);
  cell.text.style={typeface:FONT,fontFamily:FONT,fontSize:size,color:r===0?'#FFFFFF':C.ink,bold:r===0};
 }
 return t;
}
function base(d,i){
 const s=p.slides.add();s.background.fill=C.paper;
 if(d.layout!=='cover'){
  text(s,d.title,72,46,1136,116,43,true);
  text(s,d.status,72,166,1136,28,17,false,C.teal);
  text(s,d.message,72,614,1090,67,24,true);
  text(s,String(i+1).padStart(2,'0'),1180,678,32,24,15,false,C.muted);
 }
 s.speakerNotes.text=`${d.notes}\n\nMESSAGE: ${d.message}\nEVIDENCE STATUS: ${d.status}\n${d.evidence}\n\nSOURCES\n${d.sources.join('\n')}`;
 return s;
}
for(const [i,d] of story.slides.entries()){
 const s=base(d,i);
 if(d.layout==='cover'){
  s.background.fill=C.ink;
  text(s,'CULTURAL BLEND',72,62,1136,40,24,true,C.yellow);
  text(s,d.title,72,176,1136,220,72,true,'#FFFFFF');
  text(s,d.subtitle,76,427,1060,90,32,false,'#EBECEF');
  text(s,'Mike Nguyen & Sophia Nguyen',76,566,900,40,28,true,'#FFFFFF');
  text(s,'Finalists, UNSW Marketing Analytics Hackathon Challenge 2026',76,616,1110,34,23,false,C.yellow);
  text(s,'Research refresh: 2 November 2026',76,660,1060,28,18,false,'#B8BEC7');
 }else if(d.layout==='three'){
  d.items.forEach((v,j)=>{
   const x=72+j*391;
   text(s,String(j+1).padStart(2,'0'),x,235,330,76,60,true,C.teal);
   text(s,v[0],x,336,330,50,38,true);
   text(s,v[1],x,413,330,165,29);
  });
 }else if(d.layout==='population'){
  text(s,'1,453,840',72,228,640,105,81,true,C.teal);
  text(s,'valid completed durations',76,345,610,44,31,true);
  text(s,'1,453,846 input records\n6 negative durations excluded\n1,637 refunded records included',76,424,610,146,26);
  text(s,'Listing date',770,234,420,42,32,true);
  text(s,'Observed platform interval',770,306,420,62,27,false,C.teal);
  text(s,'Completed funding date',770,395,420,75,32,true);
  text(s,'96.4% pre-disbursal in the\nfull-data descriptive audit',770,507,420,72,24);
 }else if(d.layout==='benchmark'){
  const m=saved.baseline_ridge.metrics;
  // Six decimal places fit Excel's chart workbook precision; labels show two.
  // Exact saved metrics remain in the source report and speaker notes.
  const ch=s.charts.add('bar',{position:{left:72,top:228,width:770,height:345},categories:['Median baseline','Ridge','Nonlinear'],series:[{name:'Holdout MAE (days)',values:[m.baseline.holdout_mae_days,m.ridge.holdout_mae_days,saved.nonlinear_benchmark.metrics.mae_days].map(v=>Number(v.toFixed(6))),fill:C.teal}],hasLegend:false,barOptions:{direction:'column',gapWidth:90},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:22}},xAxis:{textStyle:{fontSize:22}},yAxis:{min:0,max:10,title:{text:'MAE (days)'},textStyle:{fontSize:18},majorGridlines:{fill:C.line,width:1}},chartFill:C.paper,plotAreaFill:C.paper});
  applyPresentationChartFont(ch,{fontFamily:FONT});
  text(s,'0.900',910,238,300,90,66,true,C.teal);
  text(s,'24-hour ROC AUC',914,335,290,60,27);
  text(s,'0.830',910,430,300,90,66,true,C.teal);
  text(s,'Average precision',914,527,290,50,27);
  text(s,'2024–2025 holdout: 278,887 eligible completed-funding records',76,581,1130,25,17,false,C.muted);
 }else if(d.layout==='research_benchmark'){
  const ch=s.charts.add('bar',{position:{left:72,top:224,width:800,height:350},categories:d.years.map(String),series:d.series.map(v=>({name:v.name,values:v.values.map(x=>Number(x.toFixed(6))),fill:v.color})),hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:18}},barOptions:{direction:'column',grouping:'clustered',gapWidth:70},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:16}},xAxis:{textStyle:{fontSize:21}},yAxis:{min:0,title:{text:'MAE (days)'},textStyle:{fontSize:18},majorGridlines:{fill:C.line,width:1}},chartFill:C.paper,plotAreaFill:C.paper});
  applyPresentationChartFont(ch,{fontFamily:FONT});
  text(s,d.gainLabel,918,246,290,75,57,true,C.teal);
  text(s,'Median annual\nMAE gain (days)',920,334,280,80,27);
  text(s,d.aucLabel,918,448,290,70,53,true,C.teal);
  text(s,`${d.latestYear} ROC AUC change`,920,529,280,62,24);
  text(s,'Sparse linear family; all comparisons use matching observed completed records.',76,582,1130,27,17,false,C.muted);
 }else if(d.layout==='text_gain'){
  text(s,'MAE reduction in days. Linear adds M+L+R; trees add M+L.',76,207,1125,35,23,true);
  table(s,[d.columns,...d.rows],d.widths,254,302,20);
  text(s,'Positive means lower error. M = form; L = lexicon/sentiment; R = TF-IDF. Fixed-model month-block intervals.',76,577,1125,30,17,false,C.muted);
 }else if(d.layout==='calibration'){
  const ch=s.charts.add('line',{lineOptions:{smooth:false},position:{left:72,top:222,width:1136,height:344},categories:d.binLabels,series:d.series.map(v=>({name:v.name,values:v.values.map(x=>Number(x.toFixed(6))),fill:v.color,smooth:false,marker:{symbol:'circle',size:4,fill:v.color},line:{fill:v.color,width:2}})),hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:18}},xAxis:{title:{text:'Predicted probability bin'},textStyle:{fontSize:17}},yAxis:{min:0,max:1,numberFormatCode:"0%",title:{text:'Probability / observed rate'},textStyle:{fontSize:18},majorGridlines:{fill:C.line,width:1}},chartFill:C.paper,plotAreaFill:C.paper});
  applyPresentationChartFont(ch,{fontFamily:FONT});
  text(s,d.countCaption,76,581,1125,28,16,false,C.muted);
 }else if(d.layout==='uncertainty'){
  table(s,[['Pooled region','Countries','Slope','Normal 95% interval','Heuristic interval'],['Middle East','2','−0.0729','[−0.1003, −0.0456]','[−0.2502, 0.1043]'],['Central America','2','−0.0742','[−0.0879, −0.0605]','[−0.1629, 0.0145]']],[240,155,135,300,306],231,214,23);
  text(s,'Change in log(1 + days) per extra family mention per 100 words.',76,473,1115,42,24);
  text(s,'The t(1) screen is a heuristic sensitivity calculation, not calibrated inference.',76,535,1115,64,24,false,C.muted);
 }else if(d.layout==='sensitivity'){
  text(s,'Third-person framing: Δlog(1 + days) per additional mention / 100 words',76,211,1125,43,24,true);
  table(s,[d.columns,...d.rows],d.widths,266,174,22);
  text(s,'Intervals are pointwise 95%; p-values use within-specification BH adjustment.',76,455,1125,39,21,false,C.muted);
  text(s,d.after,76,509,1125,84,24);
 }else if(d.layout==='pilot'){
  const vals=[['1','Define','Eligible new listings, truthful prompt and usual-content control.'],['2','Assign','Choose units and blocks that address contamination and spillovers.'],['3','Measure','Completion by one agreed horizon, with all eligible listings retained.'],['4','Decide','Practical effect and uncertainty, accuracy, workload and representation.']];
  vals.forEach((v,j)=>{const y=221+j*91;text(s,v[0],72,y,65,55,40,true,C.teal);text(s,v[1],160,y,180,55,29,true);text(s,v[2],364,y,835,75,26);});
 }else if(d.layout==='roadmap'){
  const vals=d.stages || [['Audit','Research / data','Claims and as-of eligibility are reconciled.'],['Benchmark','Analytics','Full-data paired gains and stability are reviewed.'],['Pilot','Platform / partners','Feasible design, endpoint and power are agreed.'],['Scale or revise','Decision owners','Practical benefit and guardrails justify the choice.']];
  vals.forEach((v,j)=>{const y=224+j*90;text(s,v[0],72,y,240,49,32,true,C.teal);text(s,v[1],340,y,280,65,24,true);text(s,v[2],657,y,548,73,26);});
 }else{
  const values=[d.columns,...d.rows];
  const h=d.after?196:(d.rows.length>=6?366:356);
  table(s,values,d.widths,210,h,d.rows.length>=5?20:23);
  if(d.after)text(s,d.after,76,446,1125,130,28);
 }
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
for(const [i,s] of p.slides.items.entries()){
 const blob=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(build,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
if(process.env.DECK_PREVIEW_ONLY === '1') {
 console.log(JSON.stringify({previewOnly:true,slides:story.slides.length,previews:path.join(build,'previews')}));
 process.exit(0);
}
const finalPath=path.join(out,path.basename(process.env.DECK_OUTPUT_NAME || 'cultural-blend-research-refresh.pptx'));
const tableSlides=story.slides.flatMap((d,i)=>['table','uncertainty','sensitivity','text_gain'].includes(d.layout)?[i+1]:[]);
const chartSlides=story.slides.flatMap((d,i)=>['benchmark','research_benchmark','calibration'].includes(d.layout)?[i+1]:[]);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,pythonExecutable:runtimePython,integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableSlides.flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:story.slides.length,requiredNativeChartOwnerSlides:chartSlides,requiredNativeTableOwnerSlides:tableSlides,materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'portable',fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,`${path.basename(finalPath)}.validation.json`)});
console.log(JSON.stringify({finalPath:result.finalPath,sha256:result.finalSha256,package:result.packageIntegrity.status,layoutFindings:result.presentationLayout.finding_count,layoutWarnings:result.presentationLayout.warnings,importPassed:result.firstPartyImport.passed}));
