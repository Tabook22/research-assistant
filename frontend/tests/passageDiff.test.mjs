import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const compiled=ts.transpileModule(readFileSync(new URL('../src/lib/passageDiff.ts',import.meta.url),'utf8'),{
 compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022},
}).outputText;
const {passageDiff}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
function verify(original,proposed){
 const parts=passageDiff(original,proposed);
 assert.equal(parts.filter(p=>p.kind!=='add').map(p=>p.text).join(''),original);
 assert.equal(parts.filter(p=>p.kind!=='remove').map(p=>p.text).join(''),proposed);
 return parts;
}
test('preserves whitespace, Arabic and English when accepting or rejecting every change',()=>{
 for(const [a,b] of [['','new'],['old',''],['same','same'],['A  claim\nwith data.','A  qualified claim\nwith data.'],['هذه نتائج أولية.','هذه نتائج أولية تحتاج إلى تحقق.']])verify(a,b);
});
test('large sections retain unchanged words around localized corrections',()=>{
 const original=Array.from({length:3000},(_,i)=>`term${i}`).join(' ');
 const proposed=original.replace('term100 ','corrected100 ').replace('term2800 ','corrected2800 ');
 const parts=verify(original,proposed);
 assert.ok(parts.filter(p=>p.kind==='equal').reduce((n,p)=>n+p.text.length,0)>original.length*.95);
});
test('large repeated sections and completely rewritten passages reconstruct exactly',()=>{
 verify('repeated claim '.repeat(2000),'new qualified finding '.repeat(2000));
 verify('start '+ 'repeated claim '.repeat(2000)+'end','start '+ 'repeated claim '.repeat(1000)+'changed '+ 'repeated claim '.repeat(1000)+'end');
});
test('mixed edits never lose or duplicate text',()=>{
 let seed=19;
 const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/2**32;};
 for(let run=0;run<60;run++){
  const a=Array.from({length:600},()=>`w${Math.floor(random()*200)} `).join('');
  const b=a.split(' ').filter(()=>random()>.1).map(w=>random()<.1?'replacement':w).join(' ');
  verify(a,b);
 }
});
