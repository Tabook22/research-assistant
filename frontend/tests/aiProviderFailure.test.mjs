import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
const code=ts.transpileModule(readFileSync(new URL('../src/lib/aiProviderFailure.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const {aiProviderFailure}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));

test('billing failures show the required action in both languages instead of waiting advice',()=>{
 for(const [code,en,ar] of [['AI_CREDIT_BALANCE','add API credits','شحن حساب API'],['AI_SPEND_LIMIT','spending limit','سقف الإنفاق'],['AI_USAGE_LIMIT','higher limit','زيادة الحد'],['AI_QUOTA','billing','الفوترة']]){
  assert.ok(aiProviderFailure(code+': private response',(en)=>en).includes(en));
  assert.ok(aiProviderFailure(code+': private response',(_,ar)=>ar).includes(ar));
  assert.ok(!aiProviderFailure(code+': private response',(en)=>en).includes('private response'));
 }
});
test('throttling is distinct and other failures retain their existing handling',()=>{
 assert.match(aiProviderFailure('AI_RATE_LIMIT: limited',(en)=>en),/Wait before retrying/);
 assert.equal(aiProviderFailure('AI_ACCESS: denied',(en)=>en),null);
});
