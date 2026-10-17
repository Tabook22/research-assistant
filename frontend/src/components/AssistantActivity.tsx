import {useI18n} from '../i18n/I18nContext';
import './assistantActivity.css';

export type AssistantCompletion = ''|'message'|'search';

export function ThinkingRobot({ready=false}:{ready?:boolean}){
 return <span className={`assistant-robot ${ready?'is-ready':'is-thinking'}`} aria-hidden="true">
  <span className="robot-floor"/>
  <span className="robot-pacer"><svg viewBox="0 0 64 64" className="robot-figure" fill="none">
   <g className="robot-body">
    <path d="M32 10V6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/><circle cx="32" cy="5" r="2.5" className="robot-antenna"/>
    <rect x="17" y="13" width="30" height="22" rx="8" className="robot-shell"/>
    <path d="M16 21h-2v6h2M48 21h2v6h-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <rect x="22" y="19" width="20" height="11" rx="4" className="robot-visor"/>
    <g className="robot-eyes"><circle cx="28" cy="24" r="1.5"/><circle cx="36" cy="24" r="1.5"/></g>
    {ready&&<path d="M29 28q3 2 6 0" className="robot-smile" strokeWidth="1.4" strokeLinecap="round"/>}
    <rect x="22" y="36" width="20" height="15" rx="5" className="robot-shell"/>
    <path d="M29 42h6M29 46h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity=".55"/>
    <g className="robot-arm robot-arm-left"><path d="M20 38l-5 8" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round"/><circle cx="14" cy="47" r="2.7" className="robot-shell"/></g>
    <g className="robot-arm robot-arm-right"><path d="M44 38l5 8" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round"/><path d="M47 46v4q0 3 3 3t3-3v-4q0-1-1-1t-1 1v-2q0-1-1-1t-1 1v2q-2-2-2 0Z" className="robot-hand"/></g>
   </g>
   <g className="robot-leg robot-leg-left"><path d="M27 51v7h-4" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round"/></g>
   <g className="robot-leg robot-leg-right"><path d="M37 51v7h4" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round"/></g>
  </svg></span>
  {ready&&<span className="robot-ready-badge"><svg viewBox="0 0 16 16" fill="none"><path d="m4 8 3 3 5-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg></span>}
 </span>;
}

export default function AssistantActivity({busy,label,completion}:{busy:string;label:string;completion:AssistantCompletion}){
 const {lang}=useI18n(),c=(en:string,ar:string)=>lang==='ar'?ar:en;
 if(!busy&&!completion)return null;
 const ready=!busy&&!!completion,robot=ready||busy==='message'||busy==='search';
 return <div className={`chat-thinking chat-thinking-visible assistant-activity ${ready?'activity-ready':''}`} role="status" aria-live="polite" aria-atomic="true">
  {robot?<ThinkingRobot ready={ready}/>:<span className="chat-thinking-spinner" aria-hidden="true"/>}
  <div className="assistant-activity-copy"><strong>{ready?(completion==='search'?c('Your search results are ready.','نتائج البحث جاهزة.'):c('Your reply is ready.','إجابتك جاهزة.')):label}</strong><small>{ready?c('You can read them above and continue the discussion.','يمكنك قراءتها أعلاه ومواصلة المناقشة.'):c('This may take a little time. You can keep reading the conversation.','قد يستغرق ذلك بعض الوقت. يمكنك متابعة قراءة المحادثة.')}</small></div>
 </div>;
}
