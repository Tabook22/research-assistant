import type {PaperChatHistory,PaperChatSession} from '../paperReviewApi';

const normalized=(text:string)=>text.normalize('NFKC').toLocaleLowerCase().replace(/[\u064b-\u065f\u0670\u0640]/g,'').replace(/[أإآ]/g,'ا').replace(/[٠-٩]/g,value=>String('٠١٢٣٤٥٦٧٨٩'.indexOf(value)));

export function localSessionDay(stamp:string|null){
 if(!stamp)return '';
 const date=new Date(stamp);if(!Number.isFinite(date.getTime()))return '';
 return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
}

export function findChatSessions(history:PaperChatHistory,query:string,day:string):PaperChatSession[]{
 const words=normalized(query).trim().split(/\s+/).filter(Boolean);
 const indexed=new Map<string,string[]>(),days=new Map<string,Set<string>>();
 for(const message of history.messages){
  if(!message.session_id)continue;
  const text=indexed.get(message.session_id)??[];text.push(message.content);indexed.set(message.session_id,text);
  const dates=days.get(message.session_id)??new Set<string>();dates.add(localSessionDay(message.created_at));days.set(message.session_id,dates);
 }
 return history.sessions.filter(session=>{
  const text=normalized([session.title,session.number,session.preview,...(indexed.get(session.id)??[])].join(' '));
  return words.every(word=>text.includes(word))&&(!day||[localSessionDay(session.created_at),localSessionDay(session.updated_at),...(days.get(session.id)??[])].includes(day));
 }).sort((a,b)=>(Date.parse(b.updated_at??b.created_at??'')||0)-(Date.parse(a.updated_at??a.created_at??'')||0)||b.number-a.number);
}
