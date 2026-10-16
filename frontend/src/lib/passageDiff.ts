export interface DiffPart {kind:'equal'|'remove'|'add';text:string}

// Preserve all whitespace and bound the LCS matrix for unusually large passages.
export function passageDiff(original:string, proposed:string):DiffPart[]{
 if(original===proposed)return [{kind:'equal',text:original}];
 const a=original.match(/\s+|[^\s]+/gu)??[], b=proposed.match(/\s+|[^\s]+/gu)??[];
 if((a.length+1)*(b.length+1)>250000)return [{kind:'remove',text:original},{kind:'add',text:proposed}];
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
