import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import ts from 'typescript';

const require=createRequire(import.meta.url);
const data=code=>'data:text/javascript;base64,'+Buffer.from(code).toString('base64');
async function load(lang){
 const code=ts.transpileModule(readFileSync(new URL('../src/components/AssistantActivity.tsx',import.meta.url),'utf8'),{
  compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX},
 }).outputText.replace('"react/jsx-runtime"',JSON.stringify(pathToFileURL(require.resolve('react/jsx-runtime')).href))
 .replace(/["']\.\.\/i18n\/I18nContext["']/,JSON.stringify(data(`export const useI18n=()=>({lang:${JSON.stringify(lang)}});`)))
 .replace(/import ["']\.\/assistantActivity\.css["'];?/, '');
 return (await import(data(code))).default;
}
const Activity=await load('en');
const render=props=>renderToStaticMarkup(React.createElement(Activity,{busy:'',label:'Thinking',completion:'',...props}));

test('idle and failed requests without a completion render no success status',()=>{
 assert.equal(render({}),'');
 assert.equal(render({completion:''}),'');
});
test('pending reply takes priority over an older completion',()=>{
 const html=render({busy:'message',completion:'message'});
 assert.match(html,/is-thinking/);assert.doesNotMatch(html,/is-ready|robot-ready-badge/);
 assert.match(html,/role="status"/);assert.match(html,/aria-hidden="true"/);
});
test('successful replies raise a hand, while session saves retain the spinner',()=>{
 const html=render({completion:'message'});
 assert.match(html,/is-ready/);assert.match(html,/robot-ready-badge/);assert.match(html,/Your reply is ready/);
 assert.doesNotMatch(render({busy:'rename'}),/assistant-robot/);
});
test('search completion and Arabic reply completion use accurate status text',async()=>{
 assert.match(render({completion:'search'}),/Your search results are ready/);
 const ArabicActivity=await load('ar');
 assert.match(renderToStaticMarkup(React.createElement(ArabicActivity,{busy:'',label:'',completion:'message'})),/إجابتك جاهزة/);
});
