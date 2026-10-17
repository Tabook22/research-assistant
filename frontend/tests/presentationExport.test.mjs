import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
import JSZip from 'jszip';
const require=createRequire(import.meta.url);
const code=ts.transpileModule(readFileSync(new URL('../src/lib/presentationDesign.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace(/['"]pptxgenjs['"]/g,JSON.stringify(pathToFileURL(require.resolve('pptxgenjs')).href));
const design=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const png='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZt8AAAAASUVORK5CYII=';
function deck(count=5){return {id:'test',count,complete:true,language:'ar',title:'منهجية البحث وإضافته العلمية',focus:'المنهجية والحدود',slides:Array.from({length:count},(_,i)=>({id:i+1,title:'عنوان الشريحة '+(i+1),focus:'شرح الإضافة وحدود الدراسة',visual:['network','process','library','globe','science','balance'][i%6],content:{bullets:['تعتمد الدراسة على تحليل مفاهيمي للوثائق','تحتاج الاستنتاجات إلى مراجعة حدود الدراسة'],notes:'ملاحظات متحدث قابلة للتحرير',location:{section_title:'المنهجية',quote:'تعتمد الدراسة على التحليل المفاهيمي للوثائق.',page:2}}}))};}

test('PowerPoint contains the exact number of editable Arabic slides, separate images and speaker notes',async()=>{
 const d=deck(5),pptx=await design.buildPowerPoint(d,'emerald',Object.fromEntries(d.slides.map(s=>[s.id,png])));
 const zip=await JSZip.loadAsync(await pptx.write({outputType:'nodebuffer'}));
 assert.equal(Object.keys(zip.files).filter(p=>/^ppt\/slides\/slide\d+\.xml$/.test(p)).length,5);
 const first=await zip.file('ppt/slides/slide1.xml').async('string');assert.ok(first.includes(d.title));assert.match(first,/rtl="1"/);assert.ok(first.includes('<p:pic>'));
 const second=await zip.file('ppt/slides/slide2.xml').async('string');assert.ok(second.includes(d.slides[1].content.bullets[0]));
 const notes=await zip.file('ppt/notesSlides/notesSlide2.xml').async('string');assert.ok(notes.includes('ملاحظات متحدث'));assert.ok(notes.includes('المنهجية'));
});
test('all theme geometries stay within the slide and keep text separate from illustration',()=>{
 for(const theme of Object.keys(design.slideThemes))for(const [index,s] of deck(20).slides.entries()){
  const g=design.slideGeometry(deck(20),s,index,theme);
  for(const b of [...g.texts,g.visual]){assert.ok(b.x>=0&&b.y>=0&&b.x+b.w<=1600&&b.y+b.h<=900);}
  for(const b of g.texts)assert.ok(b.y+b.h<=g.visual.y||b.x>=g.visual.x+g.visual.w||b.x+b.w<=g.visual.x||b.y>=g.visual.y+g.visual.h);
 }
});
test('export refuses incomplete decks and counts over twenty',async()=>{
 await assert.rejects(design.buildPowerPoint(deck(21),'emerald',{}));
 await assert.rejects(design.buildPowerPoint({...deck(),complete:false},'emerald',{}));
});
