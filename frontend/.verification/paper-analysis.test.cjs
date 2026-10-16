const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const source=ts.transpileModule(fs.readFileSync('src/paperReviewApi.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const makeReview=()=>({id:1,version:1,overview:null,sections:[1,2,3].map(id=>({id,analysis:null,original:'Synthetic source',draft:'Saved draft'}))});
function runner(request){
 const exports={};vm.runInNewContext(source,{exports,require:()=>({request})});
 return exports.analyzePaper;
}
function server(initial,failId=0){
 let saved=structuredClone(initial);const paths=[];
 const request=async(path,options)=>{
  const body=JSON.parse(options.body);assert.equal(body.version,saved.version);
  paths.push(path);
  const match=path.match(/sections\/(\d+)/);
  if(match&&Number(match[1])===failId)throw Error('AI_TIMEOUT');
  saved=structuredClone(saved);saved.version++;
  if(!match){saved.analysis_pending_ids=saved.sections.filter(s=>saved.overview||!s.analysis).map(s=>s.id);saved.overview={summary:'Synthetic overview'};}
  else{const id=Number(match[1]);saved.sections.find(s=>s.id===id).analysis={summary:'Synthetic finding'};saved.analysis_pending_ids=(saved.analysis_pending_ids??[]).filter(s=>s!==id);}
  return structuredClone(saved);
 };
 return {request,paths,saved:()=>saved};
}
test('failure retains checkpoints and resume skips completed work',async()=>{
 const initial=makeReview(),first=server(initial,2);let latest=initial;
 await assert.rejects(runner(first.request)('test',1,initial,r=>latest=r,()=>false),/AI_TIMEOUT/);
 assert.equal(latest.version,3);assert.ok(latest.overview);assert.ok(latest.sections[0].analysis);
 assert.equal(latest.sections[0].draft,'Saved draft');
 const retry=server(latest);const result=await runner(retry.request)('test',1,latest,()=>{},()=>false);
 assert.equal(retry.paths.length,2);assert.ok(retry.paths[0].includes('/sections/2/'));
 assert.ok(result.sections.every(s=>s.analysis));
});
test('pause finishes the active step without starting another request',async()=>{
 const initial=makeReview(),api=server(initial);let stopped=false;
 const result=await runner(api.request)('test',1,initial,(r,step)=>{if(r.overview&&!step)stopped=true;},()=>stopped);
 assert.equal(api.paths.length,1);assert.ok(result.overview);assert.ok(result.sections.every(s=>!s.analysis));
});
test('refresh tracks unfinished sections while retaining older findings',async()=>{
 const initial=makeReview();initial.overview={summary:'Old overview'};initial.sections.forEach(s=>s.analysis={summary:'Old finding'});
 const first=server(initial,2);let latest=initial;
 await assert.rejects(runner(first.request)('test',1,initial,r=>latest=r,()=>false),/AI_TIMEOUT/);
 assert.deepEqual(latest.analysis_pending_ids,[2,3]);assert.equal(latest.sections[1].analysis.summary,'Old finding');
 const retry=server(latest);await runner(retry.request)('test',1,latest,()=>{},()=>false);
 assert.equal(retry.paths.length,2);assert.ok(retry.paths.every(p=>p.includes('/sections/')));
});
