import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const ROOT=process.env.CHARGEAHEAD_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const OUT=process.env.CHARGEAHEAD_DECK_BUILD || path.join(ROOT,'outputs/deck/build');
await fs.mkdir(OUT,{recursive:true});
const data=JSON.parse(await fs.readFile(path.join(ROOT,'data/processed/presentation_data.json'),'utf8'));
const C={navy:'#112A35',teal:'#087F8C',lime:'#CBEA57',grey:'#6B8088',light:'#E8EFF0',paper:'#FAFCFC',white:'#FFFFFF',orange:'#BA6035'};
const FONT='DejaVu Sans';
const p=Presentation.create({slideSize:{width:1280,height:720}});
const scripts=[];
const metric=Object.fromEntries(data.primary_metrics.map(r=>[r.model,r]));
const num=v=>v.toFixed(2);
const notesSource='Numerical source: supplied workbook extracts and ChargeAhead v2 generated CSVs. Source authenticity and historical release vintages have not been independently verified. The analysis is exploratory.';
function text(s,str,x,y,w,h,size=24,color=C.navy,bold=false){
  const z=s.shapes.add({name:`text-${s.shapes.items.length}`,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
  z.text=str;z.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'top',wrap:'word',insets:0};return z;
}
function base(k,title,sub='',dark=false){
  const s=p.slides.add();s.background.fill=dark?C.navy:C.paper;
  text(s,k,64,36,1140,25,15,dark?C.lime:C.teal,true);
  text(s,title,64,86,1152,108,42,dark?C.white:C.navy,true);
  if(sub)text(s,sub,64,174,1150,54,22,dark?'#CAD7DA':C.grey);
  return s;
}
function foot(s,str){const n=p.slides.items.length;text(s,str,64,663,1090,36,13,C.grey);text(s,String(n),1180,663,36,24,14,C.grey);}
function note(s,title,seconds,en,zh,source=''){
  const i=p.slides.items.length;
  s.speakerNotes.text=`${i<=10?'MAIN TALK':'BACKUP ONLY'} | ${seconds ? seconds+' seconds target':'Use only for questions'}\n\n${en}\n\n中文提示：${zh}\n\nSources and method: ${source}\n${notesSource}`;
  scripts.push({slide:i,title,seconds,en,zh,source});
}
function table(s,values,x,y,width,height,widths,size=21){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,columnWidths:widths,values});
 t.borders.assign({style:'solid',fill:C.light,width:1});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{typeface:FONT,fontSize:size,color:C.navy},margins:{top:8,bottom:8,left:14,right:14},anchor:'center'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
   const cell=t.getCell(r,c);cell.fill=r===0?C.navy:(r%2?C.white:'#F1F6F6');cell.text.style={typeface:FONT,fontSize:size,color:r===0?C.white:C.navy,bold:r===0};
 }
 return t;
}
function chart(s,type,config){
 return s.charts.add(type,{chartFill:'none',plotAreaFill:'none',chartLine:{style:'solid',fill:'none',width:0},plotAreaLine:{style:'solid',fill:'none',width:0},hasLegend:false,
   xAxis:{textStyle:{typeface:FONT,fontSize:17,fill:C.grey},line:{style:'solid',fill:C.light,width:1}},
   yAxis:{textStyle:{typeface:FONT,fontSize:17,fill:C.grey},majorGridlines:{style:'solid',fill:C.light,width:1},line:{style:'solid',fill:'none',width:0}},...config});
}

// 1. Cover
{
 const s=p.slides.add();s.background.fill=C.navy;
 text(s,'AIPI 590   /   MID-SEMESTER REVIEW',68,63,1100,30,17,C.lime,true);
 text(s,'ChargeAhead',64,199,1120,108,82,C.white,true);
 text(s,'Can search attention improve our read\non China’s automotive transition?',68,339,1080,125,38,C.white);
 text(s,'Keming Zhou\nOctober 14, 2026',68,567,800,65,21,'#BCD0D4');
 note(s,'ChargeAhead',25,
 'ChargeAhead started with a practical question: when the car market is changing, can we see that shift earlier? Since the idea pitch, I have built the data pipeline and tested search attention against simple forecasts. Today I will show what is working, what the evidence does not yet support, and what comes next.',
 '开场讲项目动机和本次汇报范围，不承诺已经能够提前预测。','Project pitch and revised project plan.');
}
// 2. Problem / scope
{
 const s=base('PROJECT OVERVIEW','A long-term decision, a short-term test');
 text(s,'The buyer’s concern',64,239,520,45,28,C.teal,true);
 text(s,'“Will the type of car I buy\nstill fit a changing market?”',64,299,535,133,36,C.navy,true);
 text(s,'Resale value, service and parts\nmake the decision last for years.',64,468,530,87,25,C.grey);
 text(s,'What I can test now',687,239,510,45,28,C.teal,true);
 text(s,'Can search improve\nnext-month NEV retail-share\nforecasts?',687,299,500,155,28,C.navy,true);
 text(s,'Consumer context remains the goal.\nModel-level and resale predictions\nare not validated yet.',687,484,500,109,24,C.grey);
 foot(s,'NEV = new-energy vehicles, including battery electric and plug-in hybrid / range-extended vehicles.');
 note(s,'A long-term decision, a short-term test',45,
 'The original user is a car buyer. Their concern is much longer than one month: resale value, service, and parts availability. But those outcomes require evidence I do not yet have. So the midterm tests a smaller question first. Can search attention improve a forecast of the next month’s new-energy vehicle share of retail sales? That is a measurable first step toward market context for buyers. It is not yet a recommendation about a particular car or a five-year resale forecast.',
 '先把购车长期动机和期中短期检验区分清楚。NEV 在这里涵盖纯电、插混及增程。','Idea pitch, project framework; docs/PROJECT_PLAN_V2.md.');
}
// 3. Progress
{
 const s=base('PROGRESS SINCE SEPTEMBER 16','The data pipeline and first tests are complete');
 const stats=[['44','market months'],['42','search keywords'],['149','model series parsed'],['20','wholesale months']];
 stats.forEach(([v,l],i)=>{text(s,v,64+i*295,230,265,91,65,C.teal,true);text(s,l,64+i*295,328,265,58,21,C.grey);});
 table(s,[['Completed','What this gives the project'],['Cleaned and aligned source files','A reproducible monthly panel and source audit'],['Compared eight forecasting methods','A direct test of whether search adds information'],['Extracted brand and vehicle-model rows','Detailed data for the next validation stage']],64,431,1152,186,[470,682],21);
 foot(s,'New detail: 782 observed model-month values; 240 manufacturer-month wholesale records.');
 note(s,'The data pipeline and first tests are complete',45,
 'Since the pitch, the project has moved from a data plan to a working analysis pipeline. I have forty-four months of market data and forty-two search keywords. I also extracted one hundred forty-nine vehicle-model series from the supplied workbook, plus a separate manufacturer wholesale panel spanning twenty months. The core forecasting comparison is now reproducible. One scope change is that the original composite index is no longer my primary prediction target. I will explain why. The detailed data is prepared, but future model-level performance still needs to be tested.',
 '149 是车型序列，不是149个独立预测测试。20个月厂商数据也不是每家都有完整20个月。','national_panel_v2.csv; attention_monthly_long.csv; model_sales_tidy.csv; manufacturer_wholesale_monthly.csv.');
}
// 4. Data
{
 const s=base('DATA COLLECTION AND PREPARATION','Three data layers, with gaps kept visible');
 table(s,[['Data and role','Coverage','Preparation'],['Market outcomes\nCPCA extracts','44 months\nJan 2023–Aug 2026','Yearly layouts parsed\nUnits and share arithmetic checked'],['Search attention\nBaidu weekly means','42 terms / 199 weeks\nTwo terms in the main test','Completed weeks, weighted by days\nConsistent week-end attribution'],['Brand and model sales\nSeparate wholesale panel','14 brands / 6 months\n14 firms / 20 months','Missing values retained\nRetail and wholesale kept separate']],64,224,1152,302,[344,302,506],21);
 text(s,'Audit finding',64,564,205,38,23,C.orange,true);
 text(s,'Three monthly share discrepancies need source reconciliation.\n149 model series contain 112 missing model-month values.',292,559,910,72,23,C.navy);
 foot(s,'Inputs are supplied workbook extracts; original publications, release vintages and collection permissions remain to be confirmed.');
 note(s,'Three data layers, with gaps kept visible',55,
 'There are three layers. Market data defines what happened. Search attention is the candidate early signal. Brand and model records support later validation. I normalized units, aligned dates, and kept missing model values as missing rather than replacing them with zero. For search, only completed weeks enter a month’s feature. I also found three months where the reported share does not quite match the ratio of the supplied retail counts. I keep both versions and test the sensitivity. These are source extracts, so original publication dates and data vintages still need verification.',
 '数据清洗要讲动作和发现，尤其不能把缺失当0，也不能把厂商批发和品牌零售拼成一个序列。','source files in data/raw; share_source_audit.csv; docs/SOURCE_REGISTER.md.');
}
// 5. Target
{
 const s=base('TARGET DEFINITION','The target is a market share people can read','NEV retail divided by total passenger-car retail');
 const labels=data.share_history.months;
 chart(s,'line',{position:{left:51,top:240,width:797,height:355},categories:labels,series:[{name:'NEV retail share',smooth:false,values:data.share_history.values_pct.map(v=>Number(v.toFixed(6))),line:{style:'solid',fill:C.teal,width:3},marker:{symbol:'none'}}],yAxis:{min:0,max:75,majorUnit:15,numberFormatCode:'0"%"',textStyle:{typeface:FONT,fontSize:18,fill:C.grey},majorGridlines:{style:'solid',fill:C.light,width:1}}});
 text(s,'Example',902,240,305,39,23,C.teal,true);
 text(s,'55% to 57%',902,302,320,61,39,C.navy,true);
 text(s,'A +2 percentage-point\nmonthly change',902,383,305,88,25,C.navy);
 text(s,'The forecast predicts this\nchange, not absolute sales\nor a resale price.',902,498,305,100,22,C.grey);
 foot(s,'Calculated from supplied counts. The earlier four-component index is retained as an exploratory audit in the appendix.');
 note(s,'The target is a market share people can read',45,
 'The main target is now the share of passenger-car retail made up by new-energy vehicles. If that share moves from fifty-five to fifty-seven percent, the change is two percentage points. This gives us one definition across all forty-four months and a unit the audience can understand. The earlier index mixed different ideas and used a changing number of components over time. I have kept it for the audit, but removed it from the main forecast claim. Also, a rising share does not necessarily mean absolute new-energy sales are rising.',
 '用55到57的例子解释百分点。此处是份额，不是绝对需求增长。原指数保留但不作为核心目标。','national_panel_v2.csv: nev_share; legacy_component_coverage.csv.');
}
// 6. Protocol
{
 const s=base('MODEL DEVELOPMENT AND METRICS','18 monthly tests, one common comparison','March 2025–August 2026; refit each month using only available earlier rows');
 table(s,[['Comparison','What the forecast uses'],['Simple references','No change; historical mean / median; prior monthly changes'],['History only','A linear model of the previous market-share change'],['History + search','The same model, plus the previous search-attention change']],64,238,1152,248,[366,786],23);
 text(s,'MAE',64,528,130,44,31,C.teal,true);
 text(s,'How far the forecast misses,\nin percentage points',210,530,385,77,24,C.navy);
 text(s,'Direction',684,528,197,44,31,C.teal,true);
 text(s,'How often it gets\nup versus down right',910,530,300,77,24,C.navy);
 foot(s,'Timing assumption: prior-month reports are available at issuance. This is not a verified month-end, real-time backtest.');
 note(s,'18 monthly tests, one common comparison',65,
 'Each method is evaluated on the same eighteen months. At every step, the model is refitted using earlier rows only. The simple references ask whether doing very little is already competitive, such as predicting no change or a typical historical change. The key comparison then holds the model constant: market history alone versus the same history model with search added. Search is the average of two broad new-energy terms, not all forty-two keywords. Mean absolute error measures how far the prediction misses. Direction accuracy measures whether it gets up or down right. One timing limit remains: I assume the previous market report is already available when the prediction is issued.',
 '这是判断百度增量价值的核心设计。两边只差搜索输入。声明可能是月内预测，真实发布时间尚未验证。','src/analysis.py: forecast and summarize; forecast_predictions.csv; FIRST_TEST=2025-03-01.');
}
// 7. Result
{
 const s=base('PRELIMINARY RESULT','Search has not added predictive value yet','Same target, same test months, same history model');
 const names=['No change','Historical median',"Last year's change",'History only (AR1)','History + search'];
 chart(s,'bar',{position:{left:43,top:241,width:809,height:364},categories:['No\nchange','Historical\nmedian',"Last year’s\nchange",'History\nonly','History\n+ search'],series:[{name:'MAE (pp)',values:names.map(x=>Number(metric[x].mae_pp.toFixed(6))),fill:C.grey,points:names.map((_,idx)=>({idx,fill:idx===4?C.teal:idx===3?C.navy:'#9CAEB3'}))}],barOptions:{direction:'column',grouping:'clustered',gapWidth:80},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{typeface:FONT,fontSize:21,fill:C.navy,bold:true}},yAxis:{min:0,max:4,majorUnit:1,title:{text:'MAE (percentage points)',textStyle:{typeface:FONT,fontSize:17,fill:C.grey}},textStyle:{typeface:FONT,fontSize:17,fill:C.grey},majorGridlines:{style:'solid',fill:C.light,width:1}}});
 text(s,'3.22 vs 3.23',887,249,325,67,43,C.teal,true);
 text(s,'History alone / with search',887,330,320,69,22,C.grey);
 text(s,'No error reduction\nfrom adding search.',887,421,320,95,26,C.navy,true);
 text(s,'Both get direction right\nin 12 of 18 months.',887,540,320,77,23,C.grey);
 foot(s,'Lower MAE is better. Exploratory result for these two terms and this model; full eight-method comparison is in the appendix.');
 note(s,'Search has not added predictive value yet',75,
 'Here is the main result. Lower error is better. The history-only model misses by about three point two two percentage points on average. Adding search produces three point two three, so it does not improve this comparison. Both models get direction right in twelve of eighteen months. Several simple references are also competitive. Search alone performs almost exactly like predicting the historical average change. This matters because the old twenty-one-percent improvement was measured against repeating the previous month’s change, which is a weak baseline here. I cannot claim that search has added predictive information yet. The result applies to this feature definition and model, not every possible use of search data.',
 '这是重点页。强调增量尚未确认，不说所有搜索都没用。21%只赢过特定弱基线，放附录解释。','forecast_metrics.csv; legacy_index_audit.csv; full model table in appendix.');
}
// 8. Detailed outcomes
{
 const s=base('DETAILED MARKET EXPLORATION','Brand averages hide very different outcomes','March–August 2026 growth; groups follow labels in the supplied workbook');
 const g=data.brand_groups;
 chart(s,'bar',{position:{left:47,top:250,width:780,height:356},categories:['BEV\n(n=7)','BEV + EREV\n(n=4)','BEV + PHEV\n(n=2)','All three\n(n=1)'],xAxis:{tickLabelPosition:'low',textStyle:{typeface:FONT,fontSize:17,fill:C.grey}},series:[{name:'Mean',values:g.map(r=>Number((r.mean*100).toFixed(6))),fill:'#9CAEB3'},{name:'Median',values:g.map(r=>Number((r.median*100).toFixed(6))),fill:C.teal}],barOptions:{direction:'column',grouping:'clustered',gapWidth:85},hasLegend:true,legend:{position:'top',overlay:false,textStyle:{typeface:FONT,fontSize:19,fill:C.grey}},yAxis:{min:-20,max:40,majorUnit:10,numberFormatCode:'0"%"',textStyle:{typeface:FONT,fontSize:17,fill:C.grey},majorGridlines:{style:'solid',fill:C.light,width:1}}});
 text(s,'BEV + EREV group',873,263,333,42,24,C.teal,true);
 text(s,'+20% mean\n−17% median',873,330,340,127,36,C.navy,true);
 text(s,'A few fast growers can\nchange the group story.\nThis is descriptive evidence.',873,492,325,106,24,C.grey);
 foot(s,'All three = BEV + PHEV + EREV. Category-relative performance still needs a separate prediction test.');
 note(s,'Brand averages hide very different outcomes',60,
 'The detailed-data work also changed how I would describe the brand results. The earlier slide emphasized average growth. But the mean can be pulled up by one or two very fast-growing brands. In the battery-electric plus range-extended group, mean growth is about twenty percent, while the median is minus seventeen percent. I also separated a brand labeled with all three powertrains instead of hiding it inside the plug-in hybrid group. These are descriptive comparisons, not proof that the signal picked future winners. The next step is to connect a dated signal to later model performance within a clearly defined category.',
 '均值与中位数差别说明组内差异很大。品牌三动力类别单独放一组，n=1不能做群体推论。','brand_growth_v2.csv; brand_group_summary.csv; model_sales_tidy.csv.');
}
// 9. Risks
{
 const s=base('CHALLENGES AND RISK MITIGATION','Three limits determine what I can claim');
 table(s,[['Current limit','What I will do about it'],['Only 18 test months\nSeasonal moves can dominate','Keep monthly errors visible\nTest seasonal baselines on the same dates'],['Source and timing uncertainty\nHistorical releases unverified','Reconcile three share discrepancies\nVerify dates and keep the delay sensitivity'],['Market context to buyer decision\nModel and resale links untested','Test dated signals against later outcomes\nShow coverage and limitations']],64,235,1152,326,[460,692],23);
 text(s,'Responsible use',64,596,253,32,21,C.teal,true);
 text(s,'Aggregated data only. Source permissions and AI assistance documented.',327,596,887,36,21,C.grey);
 foot(s,'Customer discovery and Plause feedback are not claimed as completed; only documented evidence should be added.');
 note(s,'Three limits determine what I can claim',55,
 'Three limits matter most. First, eighteen tests are a small sample, and a few seasonal movements can change the average. I will keep the monthly errors visible and fix the next evaluation protocol before using new outcomes. Second, source quality and timing need more work, including the original release dates and the search aggregation method. Third, a market-share forecast is still several steps away from a useful decision about an individual vehicle. The dashboard should show evidence and coverage while that link is being tested. Data is aggregated, and permissions and AI assistance are documented separately.',
 '风险必须对应能执行的处理方法。不要说复杂模型一定会修复方向率。','docs/SOURCE_REGISTER.md; docs/AI_DISCLOSURE.md; forecast_sensitivity.csv.');
}
// 10. Next
{
 const s=base('NEXT STEPS TO NOVEMBER 18','A decision tool built around tested evidence');
 table(s,[['When','Deliverable','Decision gate'],['Week 1','Source and timing audit','Traceable inputs and publication dates'],['Weeks 1–2','Frozen signal comparison','Increment over the same history model'],['Weeks 2–3','Model test and user interviews','Earlier signals, later outcomes'],['By final demo','Dashboard and demo','Evidence, coverage and limitations']],64,230,1152,300,[193,448,511],22);
 text(s,'If the signal stays weak, the deliverable still reports\nwhat works, what fails, and where evidence is missing.',64,584,1140,68,27,C.teal,true);
 foot(s,'Residual values remain optional. Main talk ends here; the following slides are backup for questions.');
 note(s,'A decision tool built around tested evidence',55,
 'The next stage has clear gates. First, reconcile source definitions and availability dates. Then freeze the comparison and extend it, so that search has to beat the same model without search. Next, test whether signals dated before an outcome relate to later model performance, and interview potential users about what information would actually help them. By the final demo, the dashboard should show market composition, search evidence, and model context with coverage limits. Residual values remain optional. If the signal stays weak, that finding will remain visible in the product rather than being hidden behind a score. Thank you.',
 '结束页强调交付物和判断门槛。没有用户访谈证据就只说计划进行。讲完停在本页。','docs/PROJECT_PLAN_V2.md; supplied mid-semester guidelines and syllabus.');
}
// 11. Legacy audit
{
 const s=base('APPENDIX A   /   OLD INDEX AUDIT','Why the 21% claim moved out of the headline');
 const legacy=data.legacy_audit.filter(r=>r.index_variant==='transition_index_expanding');
 const lm=Object.fromEntries(legacy.map(r=>[r.model,r]));
 table(s,[['Original corrected index test','MAE (index units)'],['Repeat last change',lm['Repeat last change'].mae_index_units.toFixed(4)],['Search only',lm['Search only'].mae_index_units.toFixed(4)],['No change',lm['No change'].mae_index_units.toFixed(4)],['Historical median',lm['Historical median'].mae_index_units.toFixed(4)]],64,224,655,327,[490,165],23);
 text(s,'The improvement depends\non the comparator',777,241,425,94,30,C.teal,true);
 text(s,'Search beats repeated change,\nbut loses to no change.\n\nThe index also uses 2, 3 and 4\ncomponents in successive years.',777,369,425,206,24,C.navy);
 foot(s,'18 forecasts, March 2025–August 2026. Original-index units are not comparable to the new percentage-point target.');
 note(s,'Why the 21% claim moved out of the headline',0,
 'The old expanding-normalization index produces search MAE 0.0764 versus 0.0969 for repeating last change, an approximately 21% reduction. But no change gives 0.0726, which is better. Thus the result did not establish search-specific information. The original full-window and expanding-index runs also used different numbers of months, so 27% versus 21% is not a pure controlled estimate of leakage impact. The new main analysis uses a natural target and matched methods.',
 '旧21%计算没错，但不足以证明百度有效。27%和21%的月份数量也不同，不能把差值全部归因于泄漏。','legacy_index_audit.csv; legacy_component_coverage.csv; archive/v1/src/ablation.py.');
}
// 12. Metrics
{
 const s=base('APPENDIX B   /   FULL COMPARISON','All eight methods on the same 18 months');
 const vals=[['Method','MAE (pp)','RMSE (pp)','Direction']];
 for(const r of data.primary_metrics)vals.push([r.model,num(r.mae_pp),num(r.rmse_pp),r.direction_accuracy==null?'No call':`${Math.round(r.direction_accuracy*18)}/18`]);
 table(s,vals,64,213,1152,378,[525,204,221,202],20);
 text(s,'An always-up direction rule also gets 14/18 right in this sample.',64,618,1120,30,20,C.grey);
 foot(s,'No-change is evaluated on error, with zero direction-call coverage. MAE ratios are not labeled MASE.');
 note(s,'All eight methods on the same 18 months',0,
 'Historical median has the lowest MAE among these methods. Last year’s change has the lowest RMSE, illustrating that rankings depend on the metric. Search-only direction matches an always-up rule, so 14/18 alone is not evidence of a useful directional signal. The no-change method makes no directional calls. All fits use the same primary complete training rows and test dates.',
 '强调MAE和RMSE侧重点不同，零变化不算方向预测，单独报告方向覆盖率。','forecast_metrics.csv; forecast_predictions.csv.');
}
// 13. Sensitivities
{
 const s=base('APPENDIX C   /   ROBUSTNESS','Source and timing checks do not reverse the finding');
 // Read exact generated sensitivity rows, no hand-entered result numbers.
 const csv=(await fs.readFile(path.join(ROOT,'data/processed/forecast_sensitivity.csv'),'utf8')).trim().split('\n').slice(1).map(l=>l.split(','));
 const labels=[['primary','Calculated share'],['reported_share','Reported share'],['one_extra_month_delay','One extra month of delay']];
 const vals=[['Scenario','History MAE','With search MAE']];
 for(const [k,l] of labels){const h=csv.find(r=>r[0]===k&&r[1]==='History only (AR1)');const b=csv.find(r=>r[0]===k&&r[1]==='History + search');vals.push([l,Number(h[3]).toFixed(3),Number(b[3]).toFixed(3)]);}
 table(s,vals,64,224,1152,242,[586,280,286],24);
 const d=data.incremental;
 text(s,'Incremental error reduction from search',64,505,1110,39,26,C.teal,true);
 text(s,`${d.mean_mae_gain_pp.toFixed(3)} pp average; exploratory 90% block-bootstrap range\n${d.bootstrap_p05_pp.toFixed(3)} to +${d.bootstrap_p95_pp.toFixed(3)} pp includes zero.`,64,562,1112,72,25,C.navy);
 foot(s,'All scenarios use the same 18 target months. Three-month blocks, 4,000 resamples. Small-sample exploratory diagnostic.');
 note(s,'Source and timing checks do not reverse the finding',0,
 'The main comparison is unchanged when using the reported share, or when delaying both available inputs and training outcomes by an extra month. The exploratory bootstrap range spans zero. This does not supply a confirmatory hypothesis test: the sample has already been inspected and contains few observations. The extra-delay analysis predicts the monthly change, not a level forecast constructed from an unavailable intervening month.',
 '敏感性结果仍未支持增量收益。bootstrap只是小样本稳定性检查，不包装成正式统计显著性证明。','forecast_sensitivity.csv; incremental_search_diagnostic.json.');
}
// 14. Definitions and diagnostics
{
 const s=base('APPENDIX D   /   DEFINITIONS AND DIAGNOSTICS','What each signal can and cannot represent');
 table(s,[['Measure','Interpretation and limitation'],['NEV retail share','Market composition, not absolute demand growth or resale value'],['Search attention','Interest proxy; launches, news and curiosity may move searches'],['Wholesale-retail gap','Flow discrepancy; exports and scope differences can contribute'],['Brand/model sales','Descriptive outcomes; powertrain labels and entity mapping need checks']],64,219,1152,303,[380,772],22);
 text(s,'Seasonality and stationarity',64,559,510,39,25,C.teal,true);
 text(s,'STL and ADF are retained as diagnostics.\nThey do not establish predictive value or a SARIMAX order.',64,604,1125,54,21,C.grey);
 foot(s,'Source scope and variable definitions are documented in SOURCE_REGISTER.md; the primary target avoids min-max scaling.');
 note(s,'What each signal can and cannot represent',0,
 'ADF on the calculated share has p approximately 0.395 at level and 0.000282 after first differencing. This supports investigating changes but does not prove a particular seasonal model or differencing order. STL is descriptive on the observed sample. The channel ratio correlates with share in levels, but that is not independent evidence of an inventory lead and can reflect shared trends and accounting structure. Exact values and definitions are saved in the diagnostics CSV files.',
 '原始水平相关性、STL、ADF都是诊断，不是预测成功证据。批零差不要称真实库存。','share_adf.csv; share_stl.csv; descriptive_correlations.csv; docs/SOURCE_REGISTER.md.');
}
// 15. Sources & disclosure
{
 const s=base('APPENDIX E   /   SOURCES AND RESPONSIBLE USE','Source trail and AI assistance');
 table(s,[['Evidence','Reference in the project bundle'],['National market and manufacturer data','Supplied cpca_2023.xlsx through cpca_2026.xlsx'],['Search and detailed sales','baidu_index_weekly.xlsx; model_level_sales_2026.xlsx'],['Methods, results and tests','src/analysis.py; data/processed/; tests/test_analysis.py'],['Requirements and prompt record','docs/GUIDELINE_MAPPING.md; docs/AI_DISCLOSURE.md']],64,217,1152,297,[445,707],21);
 text(s,'AI assisted code, analysis checks, English text and slide design.',64,548,1150,43,24,C.teal,true);
 text(s,'Aggregated data only. Original sources and reuse permissions need confirmation.\nNo customer interviews, peer feedback or live results are invented.',64,600,1138,60,21,C.grey);
 foot(s,'Full source register and this revision’s available user prompts are included in the project documentation.');
 note(s,'Source trail and AI assistance',0,
 'OpenAI ChatGPT / Codex assisted the revision in code refactoring, analytical comparisons, integrity checks, text and presentation design. Calculations were rerun from the supplied files. Original-source authenticity, historical release vintages and access permissions were not independently verified. The available user prompts and where assistance was applied are recorded in docs/AI_DISCLOSURE.md. Earlier-session prompt records should be appended where required by course policy.',
 '按syllabus保留AI使用位置和prompt记录。不要说自动检查等同于你已完成所有人工核实。','Supplied syllabus, AI-use section; docs/AI_DISCLOSURE.md; docs/SOURCE_REGISTER.md.');
}

await fs.writeFile(path.join(OUT,'speaker_notes.json'),JSON.stringify(scripts,null,2));
let md='# ChargeAhead speaking notes\n\nMain talk: slides 1-10. Target approximately 8.5-9 minutes, with a hard stop at 10 minutes. Appendix slides are for questions only. The durations below sum to '+scripts.reduce((s,r)=>s+r.seconds,0)+' seconds; rehearse at your own pace.\n\n';
for(const r of scripts)md+=`## Slide ${r.slide}: ${r.title}\n\n${r.seconds?`Target: ${r.seconds} seconds.`:'Backup only.'}\n\n${r.en}\n\n**中文提示：** ${r.zh}\n\nSource: ${r.source}\n\n`;
await fs.writeFile(path.join(ROOT,'docs/SPEAKER_NOTES.md'),md);
await (await PresentationFile.exportPptx(p)).save(path.join(OUT,'candidate.pptx'));
// Render the exported PPTX through LibreOffice in the build workflow. The
// original artifact runtime's direct PDF renderer has a missing font module.
console.log(JSON.stringify({slides:p.slides.items.length,output:OUT,mainTalkSeconds:scripts.reduce((s,r)=>s+r.seconds,0)}));
