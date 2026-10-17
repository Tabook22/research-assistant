import {Link} from 'react-router-dom';
import {useI18n} from '../i18n/I18nContext';
import Icon from './Icon';

export default function ResearchLaunchpad({can}:{can:(permission:string)=>boolean}){
 const {lang}=useI18n(),c=(en:string,ar:string)=>lang==='ar'?ar:en;
 const actions=[
  {permission:'research_desk',to:'/desk',icon:'search' as const,tone:'mint',tag:c('DISCOVER','اكتشف'),title:c('Find your next insight','اكتشف فكرتك التالية'),description:c('Explore literature, connect evidence and ask better questions.','استكشف الدراسات واربط الأدلة واطرح أسئلة أعمق.'),action:c('Open research desk','افتح مكتب البحث')},
  {permission:'paper_review',to:'/review',icon:'spark' as const,tone:'lilac',tag:c('REFINE','طوّر'),title:c('Give your paper a fresh perspective','انظر إلى ورقتك برؤية جديدة'),description:c('Understand strengths, discuss ideas and shape a stronger manuscript.','افهم نقاط القوة وناقش الأفكار وطوّر ورقة أكثر تماسكًا.'),action:c('Review a paper','راجع ورقة بحثية')},
  {permission:'create_projects',to:'/projects/new',icon:'plus' as const,tone:'sand',tag:c('CREATE','ابدأ'),title:c('Make room for a new idea','امنح فكرتك مساحة للنمو'),description:c('Turn a question into a project with a clear research path.','حوّل سؤالك إلى مشروع بحثي ذي خطوات واضحة.'),action:c('Start a project','ابدأ مشروعًا')},
 ].filter(item=>can(item.permission)||(item.permission==='paper_review'&&can('paper_evaluate')));
 if(!actions.length)return null;
 return <section className="research-launchpad" aria-labelledby="launchpad-title"><div className="launchpad-heading"><h2 id="launchpad-title">{c('What would you like to work on?','ما الذي تود العمل عليه؟')}</h2><span>{c('A clear next step, wherever you are.','خطوة واضحة، أينما وصلت في بحثك.')}</span></div><div className="launchpad-grid">{actions.map(item=><Link to={item.to} className={`launchpad-card launchpad-${item.tone}`} key={item.to}><div className="launchpad-card-top"><span className="launchpad-icon"><Icon name={item.icon} size={23}/></span><span className="launchpad-tag">{item.tag}</span><Icon name="arrow" size={18}/></div><h3>{item.title}</h3><p>{item.description}</p><span className="launchpad-action">{item.action}</span></Link>)}</div></section>;
}
