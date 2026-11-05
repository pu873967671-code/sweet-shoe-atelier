import * as T from '../../vendor/three.module.min.js';
import {FBXLoader} from './FBXLoader.js';
import {GLTFExporter} from './GLTFExporter.js';
import {mergeVertices} from '../../vendor/addons/BufferGeometryUtils.js';
export async function convert(file){
 const input=await new FBXLoader().loadAsync('/dev/asset_candidates/hiirusama/'+file+'.fbx');input.updateMatrixWorld(true);
 const source=[];input.traverse(o=>{if(o.isMesh)source.push(o)});
 const root=new T.Group();root.name='Hiirusama_'+file;
 const box=new T.Box3().setFromObject(input),size=box.getSize(new T.Vector3()),center=box.getCenter(new T.Vector3()),scale=3/size.z;
 const names=file==='Classic_Pump'?['upper','lining','source-heel','outsole','source-cap','forefoot-sole']:['upper','source-heel','outsole','maryjane-strap','buckle'];
 for(const o of source){const src=o.geometry.index?o.geometry.toNonIndexed():o.geometry;
  for(const [j,gr] of src.groups.entries()){
   const g=new T.BufferGeometry();
   for(const name of ['position','normal','uv']){const a=src.attributes[name];if(a)g.setAttribute(name,new T.BufferAttribute(a.array.slice(gr.start*a.itemSize,(gr.start+gr.count)*a.itemSize),a.itemSize));}
   g.applyMatrix4(o.matrixWorld);const p=g.attributes.position;
   for(let i=0;i<p.count;i++)p.setXYZ(i,(p.getX(i)-center.x)*scale,(p.getY(i)-box.min.y)*scale+.012,(p.getZ(i)-center.z)*scale);
   const indexed=mergeVertices(g,1e-5);g.dispose();
   const role=names[j]||'upper';const m=new T.MeshStandardMaterial({color:role==='lining'?'#fff2e6':role.includes('sole')?'#d4bbbe':role==='buckle'?'#ead599':'#ffb5ce',roughness:.38});m.name=role;
   const mesh=new T.Mesh(indexed,m);mesh.name=role;root.add(mesh);
  }
 }
 root.userData={author:'Hiirusama',license:'CC0-1.0',source:file,units:'normalized 3-unit last',toeAxis:'+Z'};
 const binary=await new GLTFExporter().parseAsync(root,{binary:true,onlyVisible:true});
 const metrics=root.children.map(o=>{o.geometry.computeBoundingBox();return {name:o.name,vertices:o.geometry.attributes.position.count,triangles:o.geometry.index.count/3,min:o.geometry.boundingBox.min.toArray(),max:o.geometry.boundingBox.max.toArray()}});
 return {binary:Array.from(new Uint8Array(binary)),metrics};
}
