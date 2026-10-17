import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
const data=code=>'data:text/javascript;base64,'+Buffer.from(code).toString('base64');
const compile=path=>ts.transpileModule(readFileSync(new URL(path,import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const provider=data(compile('../src/lib/aiProviderFailure.ts'));
const code=compile('../src/lib/presentationFailure.ts').replace(/['"]\.\/aiProviderFailure['"]/,JSON.stringify(provider));
const {presentationFailure}=await import(data(code));
test('first-step failure does not falsely claim that slides were saved',()=>{
 const message=presentationFailure('SLIDES_FORMAT: synthetic provider text',(en,ar)=>ar,false);
 assert.ok(message.includes('بنية شرائح غير صالحة'));
 assert.ok(message.includes('لم يُحفظ عرض جديد'));
 assert.ok(!message.includes('الشرائح المحفوظة باقية'));
 assert.ok(!message.includes('synthetic provider text'));
});
test('output budgets, evidence and configuration have different actionable messages',()=>{
 assert.match(presentationFailure('AI_OUTPUT_LIMIT: limit',(en)=>en,true),/increase the analysis output token limit/);
 assert.match(presentationFailure('SLIDES_EVIDENCE: mismatch',(en)=>en,true),/only the unfinished slide/);
 assert.match(presentationFailure('AI_CONFIGURATION: error',(en)=>en,false),/structured-output support/);
 assert.match(presentationFailure('AI_TIMEOUT: error',(en)=>en,true),/timed out/);
});
test('provider billing errors retain their specific billing action',()=>{
 assert.match(presentationFailure('AI_CREDIT_BALANCE: exhausted',(en)=>en,false),/add API credits/);
});
