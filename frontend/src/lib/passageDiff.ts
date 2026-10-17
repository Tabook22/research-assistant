export interface DiffPart {kind:'equal'|'remove'|'add';text:string}

// Preserve all whitespace and bound the LCS matrix for unusually large passages.
export function passageDiff(original:string, proposed:string):DiffPart[]{
 if(original===proposed)return [{kind:'equal',text:original}];
 const a=original.match(/\s+|[^\s]+/gu)??[], b=proposed.match(/\s+|[^\s]+/gu)??[];
 if((a.length+1)*(b.length+1)>250000){
  // Unique word anchors keep long scientific sections interactive without a quadratic matrix.
  let prefix=0,suffix=0;
  while(prefix<a.length&&prefix<b.length&&a[prefix]===b[prefix])prefix++;
  while(suffix<a.length-prefix&&suffix<b.length-prefix&&a[a.length-1-suffix]===b[b.length-1-suffix])suffix++;
  if(prefix||suffix)return [
   ...(prefix?[{kind:'equal' as const,text:a.slice(0,prefix).join('')}]:[]),
   ...passageDiff(a.slice(prefix,a.length-suffix).join(''),b.slice(prefix,b.length-suffix).join('')),
   ...(suffix?[{kind:'equal' as const,text:a.slice(a.length-suffix).join('')}]:[]),
  ];
  const positions=(words:string[])=>{const map=new Map<string,number>();words.forEach((word,i)=>map.set(word,map.has(word)?-1:i));return map;};
  const left=positions(a),right=positions(b);
  const pairs:[number,number][]=[];
  for(const [word,i] of left){const j=right.get(word);if(i>=0&&j!==undefined&&j>=0&&word.trim())pairs.push([i,j]);}
  pairs.sort((x,y)=>x[0]-y[0]);
  const tails:number[]=[],previous=new Int32Array(pairs.length).fill(-1);
  pairs.forEach((pair,i)=>{let lo=0,hi=tails.length;while(lo<hi){const mid=(lo+hi)>>>1;if(pairs[tails[mid]][1]<pair[1])lo=mid+1;else hi=mid;}if(lo)previous[i]=tails[lo-1];tails[lo]=i;});
  if(!tails.length)return [{kind:'remove',text:original},{kind:'add',text:proposed}];
  const anchors:[number,number][]=[];
  for(let i=tails[tails.length-1];i>=0;i=previous[i])anchors.push(pairs[i]);
  anchors.reverse();
  const result:DiffPart[]=[];let i=0,j=0;
  for(const [x,y] of anchors){result.push(...passageDiff(a.slice(i,x).join(''),b.slice(j,y).join('')),{kind:'equal',text:a[x]});i=x+1;j=y+1;}
  result.push(...passageDiff(a.slice(i).join(''),b.slice(j).join('')));
  return result;
 }
 const matrix=Array.from({length:a.length+1},()=>new Uint16Array(b.length+1));
 for(let i=a.length-1;i>=0;i--)for(let j=b.length-1;j>=0;j--)matrix[i][j]=a[i]===b[j]?matrix[i+1][j+1]+1:Math.max(matrix[i+1][j],matrix[i][j+1]);
 const result:DiffPart[]=[];
 function append(kind:DiffPart['kind'],text:string){const last=result.at(-1);if(last?.kind===kind)last.text+=text;else result.push({kind,text});}
 let i=0,j=0;
 while(i<a.length||j<b.length){
  if(i<a.length&&j<b.length&&a[i]===b[j]){append('equal',a[i++]);j++;}
  else if(i<a.length&&(j===b.length||matrix[i+1][j]>=matrix[i][j+1]))append('remove',a[i++]);
  else append('add',b[j++]);
 }
 return result;
}
