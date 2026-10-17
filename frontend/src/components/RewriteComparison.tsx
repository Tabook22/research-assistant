import {useMemo, useState} from 'react';
import {type PaperReview, type ProposedSection} from '../paperReviewApi';
import {passageDiff} from '../lib/passageDiff';
import {useI18n} from '../i18n/I18nContext';

export interface RevisionChoice {section_id:number;mode:'source'|'enhanced'|'custom'|'omit';text:string}
interface Props {review:PaperReview;disabled:boolean;onMerge:(choices:RevisionChoice[])=>void}

export default function RewriteComparison({review,disabled,onMerge}:Props){
 const {lang}=useI18n(),c=(en:string,ar:string)=>lang==='ar'?ar:en;
 const proposal=review.rewrite!;
 const [selected,setSelected]=useState(proposal.sections[0]?.id);
 const [choices,setChoices]=useState<Record<number,RevisionChoice>>({});
 const [highlights,setHighlights]=useState(true);
 const section=proposal.sections.find(s=>s.id===selected)||proposal.sections[0];
 const source=(s:ProposedSection)=>s.source_section_ids.map(id=>{
  const snapshot=proposal.source_snapshot?.find(item=>item.id===id);
  const original=review.sections.find(item=>item.id===id);
  return snapshot?.text??(proposal.basis==='working'?(original?.draft??original?.original):original?.original)??'';
 }).join('\n\n');
 const current=choices[section.id]||{section_id:section.id,mode:'enhanced' as const,text:''};
 const before=source(section),after=section.result?.text||'';
 const parts=useMemo(()=>passageDiff(before,after),[before,after]);
 const hunks=useMemo(()=>{
  const result:{before:string;after:string;changed:boolean}[]=[];
  for(const part of parts){
   const changed=part.kind!=='equal',last=result.at(-1);
   if(changed&&last?.changed){if(part.kind==='remove')last.before+=part.text;else last.after+=part.text;}
   else result.push({before:part.kind==='add'?'':part.text,after:part.kind==='remove'?'':part.text,changed});
  }
  return result;
 },[parts]);
 const [rejected,setRejected]=useState<Record<number,number[]>>({});
 function choose(mode:RevisionChoice['mode']){
  if(mode!=='custom')setRejected(value=>({...value,[section.id]:mode==='source'?hunks.flatMap((h,i)=>h.changed?[i]:[]):[]}));
  setChoices(value=>({...value,[section.id]:{section_id:section.id,mode,text:mode==='custom'?(current.mode==='custom'?current.text:current.mode==='source'?before:after):''}}));
 }
 function toggleHunk(index:number){
  const previous=rejected[section.id]||[],next=previous.includes(index)?previous.filter(i=>i!==index):[...previous,index];
  setRejected(value=>({...value,[section.id]:next}));
  setChoices(value=>({...value,[section.id]:{section_id:section.id,mode:'custom',text:hunks.map((h,i)=>next.includes(i)?h.before:h.after).join('')}}));
 }
 const locked=disabled||!!proposal.stale;
 return <section className="revision-studio" aria-label={c('Compare and merge revisions','مقارنة ودمج التعديلات')}>
  <h3>{c('Compare, choose and merge','قارن واختر وادمج')}</h3>
  <p className="muted">{c('Review each proposed section. Keep its source, accept the enhanced wording, or combine individual changes and edit the result. Choices are unsaved until you create a merged copy.','راجع كل جزء مقترح. احتفظ بالمصدر أو اعتمد الصياغة المحسّنة أو ادمج تغييرات محددة وعدّل الناتج. لا تُحفظ اختياراتك حتى تنشئ النسخة المدمجة.')}</p>
  <div className="revision-legend"><span className="revision-removed">{c('− Removed / replaced','− محذوف / مستبدل')}</span><span className="revision-added">{c('+ Added / revised','+ مضاف / معدّل')}</span><label><input type="checkbox" checked={highlights} onChange={e=>setHighlights(e.target.checked)}/>{c('Highlight changes','إبراز التغييرات')}</label></div>
  <nav className="rewrite-outline" aria-label={c('Compare manuscript sections','مقارنة أجزاء الورقة')}>{proposal.sections.map((item,i)=><button key={item.id} className="btn" aria-pressed={item.id===section.id} onClick={()=>setSelected(item.id)}>{i+1}. {item.title} · {!item.result?c('Pending','قيد الانتظار'):choices[item.id]?.mode==='source'?c('Source','المصدر'):choices[item.id]?.mode==='custom'?c('Merged','مدمج'):choices[item.id]?.mode==='omit'?c('Omitted','مستبعد'):c('Enhanced','محسّن')}</button>)}</nav>
  <h4 dir="auto">{section.title}</h4><p dir="auto">{section.purpose}</p>
  {proposal.stale&&!proposal.source_snapshot&&<p role="status">{c('This older proposal has no saved comparison snapshot. The source below is the current text.','لا يحتوي هذا المقترح القديم على لقطة مقارنة محفوظة. النص المصدر أدناه هو النص الحالي.')}</p>}
  <div className="rewrite-comparison revision-panels"><div><h4>{proposal.basis==='original'?c('Original uploaded text','النص الأصلي المرفوع'):c('Saved working text at generation','نص العمل المحفوظ وقت التوليد')}</h4><div className="revision-reader" dir="auto">{!before?c('New section — no original counterpart.','جزء جديد — لا يوجد نص أصلي مقابل.'):!section.result||!highlights?before:parts.filter(p=>p.kind!=='add').map((p,i)=>p.kind==='remove'?<del className="revision-removed" key={i}>{p.text}</del>:<span key={i}>{p.text}</span>)}</div></div><div><h4>{c('Enhanced proposal','المقترح المحسّن')}</h4><div className="revision-reader" dir="auto">{!section.result?c('Waiting for generation…','بانتظار التوليد…'):!highlights?after:parts.filter(p=>p.kind!=='remove').map((p,i)=>p.kind==='add'?<ins className="revision-added" key={i}>{p.text}</ins>:<span key={i}>{p.text}</span>)}</div></div></div>
  {section.result&&<><div className="topbar-actions" role="group" aria-label={c('Choose section version','اختر نسخة الجزء')}>{(['source','enhanced','custom','omit'] as const).filter(mode=>mode==='omit'?!before:mode==='source'?!!before:true).map(mode=><button className="btn" disabled={locked} aria-pressed={current.mode===mode} key={mode} onClick={()=>choose(mode)}>{mode==='source'?c('Keep source','الاحتفاظ بالمصدر'):mode==='enhanced'?c('Use enhanced','استخدام المحسّن'):mode==='custom'?c('Merge & edit','دمج وتحرير'):c('Omit new section','استبعاد الجزء الجديد')}</button>)}</div>
   <details className="revision-hunks"><summary>{c('Choose individual changes','اختيار تغييرات محددة')} ({hunks.filter(h=>h.changed).length})</summary><p>{c('These controls rebuild the merge from the proposed changes. They replace any manual edits in this section.','تعيد هذه الأدوات بناء الدمج من التغييرات المقترحة وتستبدل التعديلات اليدوية في هذا الجزء.')}</p>{hunks.map((h,i)=>h.changed&&<div className="revision-hunk" key={i}><label><input type="checkbox" disabled={locked} checked={!(rejected[section.id]||[]).includes(i)} onChange={()=>toggleHunk(i)}/>{c('Use this change','استخدام هذا التغيير')}</label><div dir="auto"><del className="revision-removed">{h.before||c('[No previous text]','[لا يوجد نص سابق]')}</del></div><div dir="auto"><ins className="revision-added">{h.after||c('[Removed]','[محذوف]')}</ins></div></div>)}</details>
   {current.mode==='custom'&&<div className="field"><label htmlFor="revision-merged-text">{c('Your merged section','الجزء المدمج الخاص بك')}</label><textarea id="revision-merged-text" dir="auto" disabled={locked} maxLength={80000} value={current.text} onChange={e=>setChoices(value=>({...value,[section.id]:{...current,text:e.target.value}}))}/></div>}
   <h4>{c('Why this changed','سبب التغيير')}</h4><ul>{section.result.changes.map((change,i)=><li key={i} dir="auto">{change}</li>)}</ul>{section.result.needs_input.length>0&&<div className="rewrite-integrity"><strong>{c('Author input and verification required','استكمال وتحقق مطلوب من الباحث')}</strong><ul>{section.result.needs_input.map((need,i)=><li key={i} dir="auto">{need}</li>)}</ul></div>}
  </>}
  <button className="btn btn-primary" disabled={locked||!proposal.complete||Object.values(choices).some(item=>item.mode==='custom'&&!item.text.trim())} onClick={()=>onMerge(proposal.sections.map(s=>choices[s.id]||{section_id:s.id,mode:'enhanced',text:''}))}>{c('Create merged copy','إنشاء نسخة مدمجة')}</button><p className="muted">{c('Sections without a choice use enhanced wording. The uploaded paper stays saved; the merged copy opens separately for review and export.','تستخدم الأجزاء التي لم تختر لها نسخة الصياغة المحسّنة. تبقى الورقة المرفوعة محفوظة وتُفتح النسخة المدمجة مستقلة للمراجعة والتصدير.')}</p>
 </section>;
}
