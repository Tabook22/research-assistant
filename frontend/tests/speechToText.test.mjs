import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const compile=path=>ts.transpileModule(readFileSync(new URL(path,import.meta.url),'utf8'),{
 compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022},
}).outputText;
const url=text=>'data:text/javascript;base64,'+Buffer.from(text).toString('base64');
const language=url(compile('../src/lib/languageDetect.ts'));
const react=url('export const useState=(...a)=>globalThis.speechHooks.useState(...a); export const useRef=(...a)=>globalThis.speechHooks.useRef(...a); export const useEffect=(...a)=>globalThis.speechHooks.useEffect(...a); export const useCallback=(fn)=>fn;');
const code=compile('../src/hooks/useSpeechToText.ts').replace('"react"',JSON.stringify(react)).replace('"../lib/languageDetect"',JSON.stringify(language));
const {useSpeechToText}=await import(url(code));

function setup({supported=true,failStart=false}={}){
 const slots=[],effects=[],cleanups=[],instances=[],final=[];let index=0;
 globalThis.speechHooks={
  useState(initial){const i=index++;if(!(i in slots))slots[i]=typeof initial==='function'?initial():initial;return [slots[i],value=>{slots[i]=typeof value==='function'?value(slots[i]):value;}];},
  useRef(initial){const i=index++;return slots[i]??(slots[i]={current:initial});},
  useEffect(fn){index++;effects.push(fn);},
 };
 class Recognition{
  constructor(){instances.push(this);this.aborted=false;this.stopped=false;}
  start(){if(failStart)throw Error('Unavailable');this.onstart?.({});}
  stop(){this.stopped=true;}
  abort(){this.aborted=true;}
 }
 globalThis.window=supported?{SpeechRecognition:Recognition}:{};
 const options={mode:'ar',existingText:'',onFinalTranscript:payload=>final.push(payload)};
 function render(){index=0;const api=useSpeechToText(options);for(const effect of effects.splice(0)){const cleanup=effect();if(cleanup)cleanups.push(cleanup);}return api;}
 const api=render();
 return {api,render,instances,final,cleanup(){for(const cleanup of cleanups.reverse())cleanup();delete globalThis.window;}};
}
function result(rec,text,isFinal){rec.onresult({resultIndex:0,results:{length:1,0:{isFinal,0:{transcript:text}}}});}

test('Arabic dictation produces interim text and keeps final words delivered after stop',()=>{
 const h=setup();try{
  h.api.start();const rec=h.instances[0];assert.equal(rec.lang,'ar-SA');assert.equal(h.render().listening,true);
  result(rec,'ما مشكلة البحث',false);assert.equal(h.render().interim,'ما مشكلة البحث');assert.equal(h.final.length,0);
  h.api.stop();assert.equal(rec.stopped,true);assert.equal(rec.aborted,false);
  result(rec,'ما مشكلة البحث؟',true);rec.onend({});
  assert.deepEqual(h.final.map(p=>p.text),['ما مشكلة البحث؟']);assert.equal(h.render().listening,false);
 }finally{h.cleanup();}
});
test('permission and service failures end capture without restarting',async()=>{
 for(const error of ['not-allowed','network','audio-capture','language-not-supported']){
  const h=setup();try{
   h.api.start();const rec=h.instances[0];rec.onerror({error});rec.onend({});
   assert.equal(h.render().listening,false);assert.ok(h.render().error);
   await new Promise(resolve=>setTimeout(resolve,220));assert.equal(h.instances.length,1);
  }finally{h.cleanup();}
 }
});
test('closing the field aborts capture and disconnects late results',()=>{
 const h=setup();h.api.start();const rec=h.instances[0];h.cleanup();
 assert.equal(rec.aborted,true);assert.equal(rec.onresult,null);assert.equal(rec.onstart,null);assert.equal(rec.onend,null);
 assert.equal(h.final.length,0);
});
test('unsupported browsers and failed starts leave typing available',()=>{
 for(const options of [{supported:false},{failStart:true}]){
  const h=setup(options);try{h.api.start();assert.equal(h.render().listening,false);assert.ok(h.render().error);}finally{h.cleanup();}
 }
});
