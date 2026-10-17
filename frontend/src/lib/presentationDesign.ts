import type {PaperPresentation,PaperSlide,SlideTheme} from '../paperReviewApi';

export const slideThemes={
 emerald:{name:['Emerald academy','الأكاديمي الزمردي'],bg:'F5F4EC',ink:'173F36',accent:'167D68',soft:'DDEBE0',dark:'143E34',coverInk:'F8F5E9'},
 midnight:{name:['Midnight symposium','المؤتمر الليلي'],bg:'0F2031',ink:'F0F5F9',accent:'67CECE',soft:'203C51',dark:'0A1828',coverInk:'F0F5F9'},
 editorial:{name:['Editorial plum','التحريري الأرجواني'],bg:'FBF4EE',ink:'442C48',accent:'926581',soft:'ECDDE4',dark:'402B45',coverInk:'FFF6EC'},
} as const;
export const W=1600,H=900;
export type TextBox={text:string;x:number;y:number;w:number;h:number;font:number;color:string;bold?:boolean};

/** Keep title, body and footer in separate reserved regions in preview and PPTX. */
export function slideGeometry(deck:PaperPresentation,slide:PaperSlide,index:number,theme:SlideTheme){
 const p=slideThemes[theme],rtl=deck.language==='ar',cover=index===0;
 const visual={x:rtl?80:870,y:cover?145:265,w:650,h:cover?610:480};
 const textX=rtl?830:100;
 const texts:TextBox[]=cover?[
  {text:deck.title,x:textX,y:195,w:650,h:285,font:70,color:p.coverInk,bold:true},
  {text:slide.focus,x:textX,y:530,w:650,h:125,font:32,color:p.coverInk},
 ]:[{text:slide.title,x:100,y:65,w:1400,h:150,font:52,color:p.ink,bold:true},
  ...(slide.content?.bullets??[slide.focus]).map((text,i)=>({text,x:textX,y:275+i*149,w:625,h:125,font:39,color:p.ink}))];
 return {rtl,cover,p,visual,texts};
}

export function illustrationSvg(slide:PaperSlide,index:number,theme:SlideTheme){
 const p=slideThemes[theme],a='#'+p.accent,d='#'+p.dark,soft='#'+p.soft;
 const sw=7,shape=`fill="none" stroke="${a}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round"`;
 const motifs={
  network:`<path d="M175 185L430 150 470 405 215 440 175 185 470 405M430 150L215 440" ${shape} opacity=".45"/><circle cx="175" cy="185" r="48" fill="${a}"/><circle cx="430" cy="150" r="38" fill="${d}"/><circle cx="470" cy="405" r="58" fill="${a}"/><circle cx="215" cy="440" r="40" fill="${d}"/><circle cx="320" cy="295" r="72" fill="${soft}" stroke="${a}" stroke-width="5"/>`,
  process:`<path d="M125 175H300V310H490V445" ${shape}/><rect x="70" y="120" width="170" height="115" rx="24" fill="${a}"/><rect x="225" y="255" width="170" height="115" rx="24" fill="${d}"/><rect x="405" y="390" width="170" height="115" rx="24" fill="${a}"/><path d="M465 445l18 18 35-38" fill="none" stroke="white" stroke-width="8"/>`,
  library:`<path d="M100 180L300 220V490L100 450z" fill="${a}"/><path d="M300 220L500 170V445L300 490z" fill="${d}"/><path d="M120 145L300 180 480 135V400" ${shape}/><path d="M145 260l105 24M145 305l105 24M350 265l100-25M350 310l100-25" stroke="${soft}" stroke-width="8" stroke-linecap="round"/>`,
  globe:`<circle cx="320" cy="310" r="188" fill="${soft}"/><circle cx="320" cy="310" r="160" ${shape}/><ellipse cx="320" cy="310" rx="75" ry="160" ${shape}/><path d="M160 310h320M180 235h280M180 385h280" ${shape}/><circle cx="435" cy="190" r="23" fill="${d}"/><circle cx="205" cy="380" r="20" fill="${d}"/>`,
  science:`<circle cx="320" cy="310" r="40" fill="${a}"/><g ${shape}><ellipse cx="320" cy="310" rx="220" ry="85"/><ellipse cx="320" cy="310" rx="220" ry="85" transform="rotate(60 320 310)"/><ellipse cx="320" cy="310" rx="220" ry="85" transform="rotate(120 320 310)"/></g><circle cx="505" cy="265" r="19" fill="${d}"/>`,
  balance:`<path d="M320 130v370M200 500h240M140 220l360-45M165 215l-70 160h140zM465 180l-70 160h140z" ${shape}/><circle cx="320" cy="140" r="30" fill="${d}"/><path d="M95 375q70 60 140 0M395 340q70 60 140 0" fill="${a}"/>`,
 };
 return `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="650" viewBox="0 0 640 620"><defs><radialGradient id="g"><stop stop-color="${soft}"/><stop offset="1" stop-color="${soft}" stop-opacity="0"/></radialGradient></defs><rect width="640" height="620" fill="url(#g)"/><circle cx="320" cy="310" r="265" fill="none" stroke="${a}" stroke-opacity=".12"/><circle cx="320" cy="310" r="235" fill="none" stroke="${a}" stroke-opacity=".1"/><g transform="translate(${(index%3-1)*9} ${(index%2)*8})">${motifs[slide.visual]}</g><circle cx="100" cy="110" r="9" fill="${a}" opacity=".4"/><circle cx="555" cy="490" r="14" fill="${a}" opacity=".25"/></svg>`;
}

async function loadImage(url:string){return new Promise<HTMLImageElement>((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('Image unavailable'));image.src=url;});}
export async function illustrationPng(slide:PaperSlide,index:number,theme:SlideTheme,imageUrl?:string){
 const canvas=document.createElement('canvas');canvas.width=1000;canvas.height=800;const ctx=canvas.getContext('2d')!;
 const image=await loadImage(imageUrl??'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(illustrationSvg(slide,index,theme)));
 if(imageUrl){const scale=Math.max(1000/image.width,800/image.height);ctx.drawImage(image,(1000-image.width*scale)/2,(800-image.height*scale)/2,image.width*scale,image.height*scale);}
 else ctx.drawImage(image,0,0,1000,800);
 return canvas.toDataURL('image/png');
}
function lines(ctx:CanvasRenderingContext2D,text:string,width:number){
 const result:string[]=[];let line='';
 for(const word of text.split(/\s+/)){
  if(ctx.measureText(word).width>width){
   if(line){result.push(line);line='';}
   for(const char of Array.from(word)){if(ctx.measureText(line+char).width>width&&line){result.push(line);line=char;}else line+=char;}
  }else{const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){result.push(line);line=word;}else line=next;}
 }
 if(line)result.push(line);return result;
}
export function fitText(box:TextBox,ctx:CanvasRenderingContext2D){
 let font=box.font;while(font>30){ctx.font=`${box.bold?'bold ':''}${font}px Arial`;if(lines(ctx,box.text,box.w).length*font*1.35<=box.h)break;font-=1;}
 ctx.font=`${box.bold?'bold ':''}${font}px Arial`;return {font,lines:lines(ctx,box.text,box.w)};
}
export async function renderSlide(deck:PaperPresentation,slide:PaperSlide,index:number,theme:SlideTheme,imageUrl?:string){
 const canvas=document.createElement('canvas');canvas.width=W;canvas.height=H;const ctx=canvas.getContext('2d')!,g=slideGeometry(deck,slide,index,theme);
 ctx.fillStyle='#'+(g.cover?g.p.dark:g.p.bg);ctx.fillRect(0,0,W,H);
 ctx.fillStyle='#'+g.p.accent;ctx.fillRect(g.rtl?W-22:0,0,22,H);
 const art=await loadImage(await illustrationPng(slide,index,theme,imageUrl));ctx.drawImage(art,g.visual.x,g.visual.y,g.visual.w,g.visual.h);
 ctx.direction=g.rtl?'rtl':'ltr';ctx.textAlign=g.rtl?'right':'left';ctx.textBaseline='top';
 for(const box of g.texts){const fit=fitText(box,ctx);ctx.fillStyle='#'+box.color;fit.lines.forEach((line,i)=>ctx.fillText(line,g.rtl?box.x+box.w:box.x,box.y+i*fit.font*1.35));}
 ctx.direction='ltr';ctx.font='22px Arial';ctx.fillStyle='#'+(g.cover?g.p.coverInk:g.p.accent);ctx.fillText(String(index+1).padStart(2,'0')+' / '+deck.count,g.rtl?1480:120,825);
 return canvas.toDataURL('image/png');
}

/** Text and presenter notes remain editable; graphics are separate PNG assets. */
export async function buildPowerPoint(deck:PaperPresentation,theme:SlideTheme,art:Record<number,string>,fontSizes?:Record<number,number[]>){
 if(deck.count>20||deck.slides.length!==deck.count||!deck.complete||deck.slides.some(s=>!s.content))throw new Error('Complete a presentation of at most 20 slides before exporting.');
 const {default:PptxGenJS}=await import('pptxgenjs');const pptx=new PptxGenJS();pptx.layout='LAYOUT_WIDE';pptx.author='ResearchGuide';pptx.subject=deck.focus;pptx.title=deck.title;pptx.company='ResearchGuide';pptx.rtlMode=deck.language==='ar';pptx.theme={headFontFace:'Arial',bodyFontFace:'Arial'};
 const k=13.333333/W;
 for(const [index,item] of deck.slides.entries()){
  const g=slideGeometry(deck,item,index,theme),slide=pptx.addSlide();slide.background={color:g.cover?g.p.dark:g.p.bg};
  slide.addShape(pptx.ShapeType.rect,{x:g.rtl?13.15:0,y:0,w:.1833,h:7.5,line:{transparency:100},fill:{color:g.p.accent}});
  if(art[item.id])slide.addImage({data:art[item.id],x:g.visual.x*k,y:g.visual.y*k,w:g.visual.w*k,h:g.visual.h*k});
  for(const [j,box] of g.texts.entries())slide.addText(box.text,{x:box.x*k,y:box.y*k,w:box.w*k,h:box.h*k,fontFace:'Arial',fontSize:(fontSizes?.[item.id]?.[j]??box.font)*.6,bold:box.bold,color:box.color,margin:0,breakLine:false,rtlMode:g.rtl,lang:deck.language==='ar'?'ar-OM':'en-GB',align:g.rtl?'right':'left',valign:'top',lineSpacingMultiple:1.15,paraSpaceAfter:0});
  slide.addText(String(index+1).padStart(2,'0')+' / '+deck.count,{x:g.rtl?11.1:1,y:6.87,w:1.2,h:.25,fontSize:13,color:g.cover?g.p.coverInk:g.p.accent,align:g.rtl?'right':'left',margin:0});
  const loc=item.content!.location;slide.addNotes(item.content!.notes+'\n\n'+(deck.language==='ar'?'المصدر: ':'Source: ')+loc.section_title+(loc.page?' · '+loc.page:'')+'\n'+loc.quote+'\n\n'+(item.image_ready?'AI-generated conceptual illustration; not research evidence.':'Conceptual illustration; not a data chart.')+(item.content!.edited?'\nResearcher edited this slide.':''));
 }
 return pptx;
}

export async function exportPowerPoint(deck:PaperPresentation,theme:SlideTheme,images:Record<number,string>){
 const art:Record<number,string>={},sizes:Record<number,number[]>={};const ctx=document.createElement('canvas').getContext('2d')!;
 for(const [index,slide] of deck.slides.entries()){art[slide.id]=await illustrationPng(slide,index,theme,images[slide.id]);sizes[slide.id]=slideGeometry(deck,slide,index,theme).texts.map(t=>fitText(t,ctx).font);}
 const pptx=await buildPowerPoint(deck,theme,art,sizes);await pptx.writeFile({fileName:(deck.title.replace(/[\\/:*?"<>|]/g,'').slice(0,80)||'Research presentation')+'.pptx'});
}
