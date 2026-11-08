export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
  const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',...options.headers}});
  if(!response.ok){const data=await response.json().catch(()=>({detail:response.statusText}));throw new Error(Array.isArray(data.detail)?data.detail.map((e:{loc:string[];msg:string})=>`${e.loc.join('.')}: ${e.msg}`).join(' · '):data.detail||'Request failed');}
  return response.json();
}
export function download(name:string,content:string,type='application/json'){
  const url=URL.createObjectURL(new Blob([content],{type}));const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}

// Compare meaning, not JSON property insertion order or unused gate defaults.
export function sameConfig(a:unknown,b:unknown):boolean {
  function canonical(value:unknown):unknown {
    if(Array.isArray(value))return value.map(canonical);
    if(value!==null&&typeof value==='object'){
      const object=value as Record<string,unknown>;
      return Object.fromEntries(Object.keys(object).sort().filter(k=>object[k]!==undefined&&object[k]!==null&&!(k==='angle'&&typeof object.name==='string'&&!['RX','RY','RZ','P','CP'].includes(object.name))).map(k=>[k,canonical(object[k])]));
    }
    return value;
  }
  return JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
}
