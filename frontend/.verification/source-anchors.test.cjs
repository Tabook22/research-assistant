const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const exportsForTest={};
const source=ts.transpileModule(fs.readFileSync('src/lib/sourceAnchors.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
vm.runInNewContext(source,{exports:exportsForTest});
const {sourceAnchor}=exportsForTest;
test('Arabic evidence after emoji maps code points to correct editor selection',()=>{
 const text='🙂 مقدمة\nنبحث في حماية البيئة البحرية.';const quote='نبحث في حماية';
 const start=Array.from(text.slice(0,text.indexOf(quote))).length;
 const anchor=sourceAnchor(text,{start,end:start+Array.from(quote).length,quote});
 assert.equal(anchor.quote,quote);assert.equal(text.slice(anchor.selectionStart,anchor.selectionEnd),quote);
 assert.equal(anchor.before+anchor.quote+anchor.after,text);
});
test('stale or invalid anchors never highlight unrelated text',()=>{
 assert.equal(sourceAnchor('New researcher draft',{start:0,end:3,quote:'Old'}),null);
 assert.equal(sourceAnchor('Text',{start:-1,end:2,quote:'Te'}),null);
 assert.equal(sourceAnchor('Text',{start:0,end:99,quote:'Text'}),null);
});
