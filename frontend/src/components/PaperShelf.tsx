import {useState} from 'react';
import type {ReviewSummary} from '../paperReviewApi';
import {useI18n} from '../i18n/I18nContext';
import Icon from './Icon';
import './paperStudio.css';

export default function PaperShelf({items,selected,disabled,onOpen}:{items:ReviewSummary[];selected?:number;disabled:boolean;onOpen:(id:number)=>void}){
 const {lang}=useI18n(),ar=lang==='ar',c=(en:string,arabic:string)=>ar?arabic:en;
 const [expanded,setExpanded]=useState(false);
 if(!items.length)return null;
 return <section className="paper-shelf" aria-label={c('Your saved papers','أوراقك المحفوظة')}><div className="paper-shelf-heading"><div><span className="eyebrow">{c('YOUR RESEARCH COLLECTION','مجموعتك البحثية')}</span><h2>{c('Pick up where you left off','أكمل من حيث وصلت')}</h2></div>{items.length>4&&<button className="btn btn-ghost" aria-expanded={expanded} onClick={()=>setExpanded(!expanded)}>{expanded?c('Show fewer','عرض أقل'):c(`All papers (${items.length})`,`كل الأوراق (${items.length})`)}</button>}</div><div className="paper-shelf-grid">{(expanded?items:items.slice(0,4)).map(item=><button className={`paper-tile ${selected===item.id?'selected':''}`} key={item.id} aria-pressed={selected===item.id} disabled={disabled} onClick={()=>onOpen(item.id)}><span className="paper-tile-icon"><Icon name="book" size={25}/><span className="paper-tile-lines" aria-hidden="true"/></span><span className="paper-tile-info"><strong dir="auto">{item.filename}</strong><small>{item.analysis_mode==='structure_only'?c('Extracted · ready to explore','نص مستخرج · جاهز للاستكشاف'):c('Saved review','مراجعة محفوظة')}</small><span>{selected===item.id?c('Currently open','مفتوحة الآن'):c('Open paper','افتح الورقة')} <Icon name="arrow" size={15}/></span></span></button>)}</div></section>;
}
