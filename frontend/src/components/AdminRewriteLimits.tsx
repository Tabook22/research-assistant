import {useEffect,useState,type FormEvent} from 'react';
import {request} from '../api';
import {useI18n} from '../i18n/I18nContext';
import type {RewriteLimits} from '../paperReviewApi';
import './adminRewriteLimits.css';

type Scope='global'|'project'|'review';
type Mode='inherit'|'custom'|'unlimited';
type Policy=RewriteLimits&{version:number;mode:Mode};
type Data={policy:Policy;effective:RewriteLimits};
interface Props {token:string;scope:Scope;targetId:number;disabled?:boolean;onSaved?:(limits:RewriteLimits)=>void}

export function RewriteLimitsEditor({token,scope,targetId,disabled=false,onSaved}:Props){
 const {lang}=useI18n(),c=(en:string,ar:string)=>lang==='ar'?ar:en;
 const [data,setData]=useState<Data|null>(null),[mode,setMode]=useState<Mode>('inherit');
 const [source,setSource]=useState('110000'),[output,setOutput]=useState('105000'),[discussion,setDiscussion]=useState('80000');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[attempt,setAttempt]=useState(0);
 const endpoint=`/admin/rewrite-limits/${scope}/${targetId}`;
 function accept(value:Data){setData(value);setMode(value.policy.mode);const limits=value.policy.mode==='custom'?value.policy:value.effective;setSource(String(limits.source_limit??110000));setOutput(String(limits.output_limit??105000));setDiscussion(String(limits.discussion_limit??80000));}
 useEffect(()=>{let active=true;setData(null);setError('');setNotice('');request<Data>(endpoint,{},token).then(value=>{if(active)accept(value);}).catch(()=>{if(active)setError(c('Could not load the policy. Retry below.','تعذر تحميل الإعداد. أعد المحاولة أدناه.'));});return()=>{active=false;};},[token,scope,targetId,attempt]);
 async function save(event:FormEvent){event.preventDefault();if(!data)return;setBusy(true);setError('');setNotice('');
  try{const next=await request<Data>(endpoint,{method:'PUT',body:JSON.stringify({version:data.policy.version,mode,source_limit:mode==='custom'?Number(source):null,output_limit:mode==='custom'?Number(output):null,discussion_limit:mode==='custom'?Number(discussion):null})},token);accept(next);onSaved?.(next.effective);setNotice(c('Saved. Applies to the next generation step, including a resumed proposal.','حُفظ الإعداد ويُطبّق في خطوة التوليد التالية، بما فيها استئناف المقترح.'));}
  catch(e){setError((e as Error).message.includes('REWRITE_POLICY_CHANGED')?c('Another administrator changed this policy. Reload it before saving.','غيّر مسؤول آخر هذا الإعداد. أعد تحميله قبل الحفظ.'):c('Could not save. Check the character ceilings and retry.','تعذر الحفظ. تحقق من سقوف الأحرف ثم أعد المحاولة.'));}finally{setBusy(false);}
 }
 const number=(value:number|null)=>value===null?c('No app limit','بلا حد من التطبيق'):value.toLocaleString(lang==='ar'?'ar-OM':'en-GB');
 return <form className="rewrite-policy-editor" onSubmit={e=>void save(e)}><p>{scope==='global'?c('Default for all papers. A project or paper exception takes priority.','الإعداد الافتراضي لكل الأوراق. يتقدم عليه استثناء المشروع أو الورقة.'):scope==='project'?c('Applies only to papers in this project unless a paper has its own exception.','يسري فقط على أوراق هذا المشروع، ما لم تُحدد للورقة سياسة مستقلة.'):c('Applies only to this paper. Other papers retain their existing limits.','يسري على هذه الورقة فقط. تحتفظ الأوراق الأخرى بسقوفها الحالية.')}</p>
 {!data&&!error&&<p role="status">{c('Loading policy…','جارٍ تحميل الإعداد…')}</p>}
 {data&&<><div className="rewrite-policy-effective"><strong>{c('Currently applied','الإعداد المطبّق حاليًا')} · {data.effective.scope==='review'?c('Paper exception','استثناء الورقة'):data.effective.scope==='project'?c('Project exception','استثناء المشروع'):c('General policy','الإعداد العام')}</strong><span>{c('Source','المصدر')}: {number(data.effective.source_limit)} · {c('Generated text','النص المولّد')}: {number(data.effective.output_limit)} · {c('Discussion context','سياق المناقشة')}: {number(data.effective.discussion_limit)}</span></div>
 <fieldset disabled={disabled||busy}><div className="field"><label htmlFor={`rewrite-mode-${scope}-${targetId}`}>{c('Character ceiling policy','سياسة سقف الأحرف')}</label><select id={`rewrite-mode-${scope}-${targetId}`} value={mode} onChange={e=>setMode(e.target.value as Mode)}>{scope!=='global'&&<option value="inherit">{c('Inherit project / general policy','وراثة إعداد المشروع / الإعداد العام')}</option>}<option value="custom">{c('Custom character ceilings','سقوف أحرف مخصصة')}</option>{scope!=='global'&&<option value="unlimited">{c('No application character ceiling','بلا سقف أحرف من التطبيق')}</option>}</select></div>
 {mode==='custom'&&<div className="rewrite-policy-fields">{[
  {id:'source',label:c('Maximum source characters','الحد الأقصى لأحرف المصدر'),value:source,set:setSource},
  {id:'output',label:c('Maximum generated characters','الحد الأقصى للأحرف المولّدة'),value:output,set:setOutput},
  {id:'discussion',label:c('Maximum saved discussion characters','الحد الأقصى لأحرف المناقشات المحفوظة'),value:discussion,set:setDiscussion},
 ].map(field=><div className="field" key={field.id}><label htmlFor={`rewrite-cap-${scope}-${targetId}-${field.id}`}>{field.label}</label><input id={`rewrite-cap-${scope}-${targetId}-${field.id}`} type="number" min={1} max={2000000000} step={1} required value={field.value} onChange={e=>field.set(e.target.value)}/></div>)}</div>}
 <p className="rewrite-policy-note">{c('Unlimited removes these application character ceilings; it does not increase provider balance, rate limits, model context, per-response token limits, upload limits or assessment capacity. Longer tasks can cost more and still need continuation after a provider failure.','«بلا سقف» يلغي حدود الأحرف هذه داخل التطبيق؛ لا يزيد رصيد المزوّد أو معدل طلباته أو سعة سياق الموديل أو رموز الإجابة الواحدة أو حدود الرفع أو سعة التقييم. قد ترتفع تكلفة المهام الطويلة وتحتاج إلى متابعة بعد تعطل المزوّد.')}</p><button type="submit" className="btn btn-primary">{busy?c('Saving…','جارٍ الحفظ…'):c('Save administrator policy','حفظ إعداد الأدمن')}</button></fieldset></>}
 {error&&<div className="error review-alert" role="alert">{error}<button className="btn" type="button" disabled={busy||disabled} onClick={()=>setAttempt(n=>n+1)}>{c('Reload policy','إعادة تحميل الإعداد')}</button></div>}{notice&&<p className="success-box" role="status">{notice}</p>}</form>;
}

export default function RewriteLimitControl(props:Props){
 const {lang}=useI18n();const [expanded,setExpanded]=useState(false);
 return <details className="rewrite-policy-control" onToggle={event=>setExpanded(event.currentTarget.open)}><summary>{lang==='ar'?'إعداد الأدمن: سقف إعادة الصياغة':'Administrator: revision character ceilings'}</summary>{expanded&&<RewriteLimitsEditor {...props}/>}</details>;
}
