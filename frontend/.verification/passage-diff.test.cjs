const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const exportsForTest={};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/passageDiff.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:exportsForTest});
const {passageDiff}=exportsForTest;
function verify(a,b){const parts=passageDiff(a,b);assert.equal(parts.filter(p=>p.kind!=='add').map(p=>p.text).join(''),a);assert.equal(parts.filter(p=>p.kind!=='remove').map(p=>p.text).join(''),b);return parts;}
test('Arabic, English, emoji and whitespace survive source/proposal comparison',()=>{
 const parts=verify('🙂 هذه دراسة\nعن التعليم.','🙂 هذه دراسة\nعن إتاحة التعليم.');
 assert(parts.some(p=>p.kind==='add'&&p.text.includes('إتاحة')));
 assert(parts.some(p=>p.kind==='equal'&&p.text.includes('هذه')));
 verify('A claim.  More evidence?','A qualified claim.\nMore evidence.');
});
test('unchanged, empty and long passages reconstruct both versions',()=>{
 assert.equal(verify('No change','No change')[0].kind,'equal');
 verify('','New text');verify('Removed','');verify('','');
 const parts=verify('word '.repeat(600),'changed '.repeat(600));
 assert.equal(parts.length,2);
});
