const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const exportsForTest={};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/chatSessions.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:exportsForTest});
const {findChatSessions,localSessionDay}=exportsForTest;
const session=(id,number,title,stamp)=>({id,number,title,created_at:stamp,updated_at:stamp,preview:'',question_count:0,message_count:0,search_count:0});
test('session index finds Arabic questions and stable numbers without mixing transcripts',()=>{
 const history={sessions:[session('one',1,'المنهج','2026-10-17T10:00:00Z'),session('two',2,'مناقشة النتائج','2026-10-18T10:00:00Z')],messages:[{session_id:'one',content:'كيف أحسّن مُشكلة البحث؟',created_at:'2026-10-17T10:00:00Z'},{session_id:'two',content:'Compare the results with related work.',created_at:'2026-10-18T10:00:00Z'}],searches:[]};
 assert.equal(findChatSessions(history,'احسن مشكلة','')[0].id,'one');
 assert.equal(findChatSessions(history,'٢','')[0].id,'two');
 assert.equal(findChatSessions(history,'related work','')[0].id,'two');
 assert.equal(findChatSessions(history,'missing keywords','').length,0);
 assert.equal(findChatSessions(history,'','')[0].id,'two');
});
test('activity-date filter includes resumed discussion days and handles undated legacy sessions',()=>{
 const history={sessions:[session('one',1,'Earlier discussion','2026-10-17T10:00:00Z'),session('legacy',2,'Undated',null)],messages:[{session_id:'one',content:'Continued later',created_at:'2026-10-20T10:00:00Z'}],searches:[]};
 assert.equal(findChatSessions(history,'',localSessionDay('2026-10-20T10:00:00Z'))[0].id,'one');
 assert.equal(findChatSessions(history,'','2026-01-01').length,0);
 assert.equal(localSessionDay(null),'');assert.equal(localSessionDay('invalid'),'');
 assert.equal(findChatSessions(history,'Undated','')[0].id,'legacy');
});
